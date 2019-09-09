#AUTOGENERATED! DO NOT EDIT! File to edit: dev/33_test_models_core.ipynb (unless otherwise specified).

__all__ = ['LinearDecoder', 'SequentialRNN', 'get_language_model']

#Cell
from ...torch_basics import *
from ...test import *
from ...core import *
from ...layers import *
from ...data.transform import *
from ...data.core import *
from ...data.source import *
from ...data.external import *
from ...data.pipeline import *
from ..core import *
from ...notebook.showdoc import show_doc
from .awdlstm import *

#Cell
_model_meta = {AWD_LSTM: {'hid_name':'emb_sz', 'url':URLs.WT103_FWD, 'url_bwd':URLs.WT103_BWD,
                          'config_lm':awd_lstm_lm_config, 'split_lm': awd_lstm_lm_split,
                          'config_clas':awd_lstm_clas_config, 'split_clas': awd_lstm_clas_split},
               AWD_QRNN: {'hid_name':'emb_sz',
                          'config_lm':awd_qrnn_lm_config, 'split_lm': awd_lstm_lm_split,
                          'config_clas':awd_qrnn_clas_config, 'split_clas': awd_lstm_clas_split},}
              # Transformer: {'hid_name':'d_model', 'url':URLs.OPENAI_TRANSFORMER,
              #               'config_lm':tfmer_lm_config, 'split_lm': tfmer_lm_split,
              #               'config_clas':tfmer_clas_config, 'split_clas': tfmer_clas_split},
              # TransformerXL: {'hid_name':'d_model',
              #                'config_lm':tfmerXL_lm_config, 'split_lm': tfmerXL_lm_split,
              #                'config_clas':tfmerXL_clas_config, 'split_clas': tfmerXL_clas_split}}

#Cell
class LinearDecoder(Module):
    "To go on top of a RNNCore module and create a Language Model."
    initrange=0.1

    def __init__(self, n_out, n_hid, output_p=0.1, tie_encoder=None, bias=True):
        self.decoder = nn.Linear(n_hid, n_out, bias=bias)
        self.decoder.weight.data.uniform_(-self.initrange, self.initrange)
        self.output_dp = RNNDropout(output_p)
        if bias: self.decoder.bias.data.zero_()
        if tie_encoder: self.decoder.weight = tie_encoder.weight

    def forward(self, input):
        raw_outputs, outputs = input
        decoded = self.decoder(self.output_dp(outputs[-1]))
        return decoded, raw_outputs, outputs

#Cell
class SequentialRNN(nn.Sequential):
    "A sequential module that passes the reset call to its children."
    def reset(self):
        for c in self.children(): getattr(c, 'reset', noop)()

#Cell
def get_language_model(arch, vocab_sz, config=None, drop_mult=1.):
    "Create a language model from `arch` and its `config`."
    meta = _model_meta[arch]
    config = ifnone(config, meta['config_lm']).copy()
    for k in config.keys():
        if k.endswith('_p'): config[k] *= drop_mult
    tie_weights,output_p,out_bias = map(config.pop, ['tie_weights', 'output_p', 'out_bias'])
    init = config.pop('init') if 'init' in config else None
    encoder = arch(vocab_sz, **config)
    enc = encoder.encoder if tie_weights else None
    decoder = LinearDecoder(vocab_sz, config[meta['hid_name']], output_p, tie_encoder=enc, bias=out_bias)
    model = SequentialRNN(encoder, decoder)
    return model if init is None else model.apply(init)