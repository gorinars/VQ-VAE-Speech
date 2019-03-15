 #####################################################################################
 # MIT License                                                                       #
 #                                                                                   #
 # Copyright (C) 2019 Charly Lamothe                                                 #
 #                                                                                   #
 # This file is part of VQ-VAE-Speech.                                               #
 #                                                                                   #
 #   Permission is hereby granted, free of charge, to any person obtaining a copy    #
 #   of this software and associated documentation files (the "Software"), to deal   #
 #   in the Software without restriction, including without limitation the rights    #
 #   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell       #
 #   copies of the Software, and to permit persons to whom the Software is           #
 #   furnished to do so, subject to the following conditions:                        #
 #                                                                                   #
 #   The above copyright notice and this permission notice shall be included in all  #
 #   copies or substantial portions of the Software.                                 #
 #                                                                                   #
 #   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR      #
 #   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,        #
 #   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE     #
 #   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER          #
 #   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,   #
 #   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE   #
 #   SOFTWARE.                                                                       #
 #####################################################################################

from vq_vae_speech.speech_encoder import SpeechEncoder
from vq_vae_speech.speech_features import SpeechFeatures
from vq_vae_features.features_decoder import FeaturesDecoder
from vq.vector_quantizer import VectorQuantizer
from vq.vector_quantizer_ema import VectorQuantizerEMA

import torch.nn as nn
import torch


class FeaturesAutoEncoder(nn.Module):
    
    def __init__(self, configuration, device):
        super(FeaturesAutoEncoder, self).__init__()

        self._encoder = SpeechEncoder(
            in_channels=configuration['features_dim'],
            num_hiddens=configuration['num_hiddens'],
            num_residual_layers=configuration['num_residual_layers'],
            num_residual_hiddens=configuration['num_hiddens'],
            use_kaiming_normal=configuration['use_kaiming_normal'],
            input_features_type=configuration['input_features_type'],
            features_filters=configuration['features_filters'],
            device=device
        )

        self._pre_vq_conv = nn.Conv1d(
            in_channels=configuration['num_embeddings'],
            out_channels=configuration['embedding_dim'],
            kernel_size=1,
            stride=1
        )

        if configuration['decay'] > 0.0:
            self._vq = VectorQuantizerEMA(
                num_embeddings=configuration['embedding_dim'],
                embedding_dim=configuration['num_embeddings'],
                commitment_cost=configuration['commitment_cost'],
                decay=configuration['decay'],
                device=device
            )
        else:
            self._vq = VectorQuantizer(
                num_embeddings=configuration['embedding_dim'],
                embedding_dim=configuration['num_embeddings'],
                commitment_cost=configuration['commitment_cost'],
                device=device
            )

        self._decoder = FeaturesDecoder(
            in_channels=configuration['embedding_dim'],
            out_channels=configuration['features_dim'],
            num_hiddens=configuration['num_embeddings'],
            num_residual_layers=configuration['num_residual_layers'],
            num_residual_hiddens=configuration['residual_channels'],
            use_kaiming_normal=configuration['use_kaiming_normal'],
            use_jitter=configuration['use_jitter'],
            jitter_probability=configuration['jitter_probability']
        )

        self._criterion = nn.MSELoss()
        self._device = device
        self._features_filters = configuration['features_filters']
        self._output_features_type = configuration['output_features_type']
        self._features_dim = configuration['features_dim']

    @property
    def vq(self):
        return self._vq

    @property
    def pre_vq_conv(self):
        return self._pre_vq_conv

    @property
    def encoder(self):
        return self._encoder

    @property
    def decoder(self):
        return self._decoder

    def forward(self, x, y):
        z = self._encoder(x)

        z = self._pre_vq_conv(z)

        vq_loss, quantized, perplexity, _ = self._vq(z)

        reconstructed_x = self._decoder(quantized)

        reconstructed_x = reconstructed_x.view(self._features_dim, self._features_filters * 3)
        y_features = SpeechFeatures.features_by_name(self._output_features_type, y)
        tensor_y_features = torch.tensor(y_features).to(self._device)

        reconstruction_loss = self._criterion(reconstructed_x, tensor_y_features)
        loss = vq_loss + reconstruction_loss

        return loss, reconstructed_x, perplexity

    def save(self, path):
        torch.save(self.state_dict(), path)

    @staticmethod
    def load(self, path, configuration, device):
        model = FeaturesAutoEncoder(configuration, device)
        model.load_state_dict(torch.load(path, map_location=device))
        return model