# -*- coding: utf-8 -*-

import json
import re
import os
import torch
import numpy as np
from torch.utils.data import Dataset, DataLoader
from transformers import BertTokenizer
"""
数据加载
"""


class DataGenerator:
    def __init__(self, data_path, config):
        self.config = config
        self.path = data_path
        self.label_to_index = self.load_schema(config.schema_path)
        self.index_to_label = dict((y, x) for x, y in self.label_to_index.items())
        self.config.class_num = len(self.index_to_label)
        if self.config.model_type == "bert":
            self.tokenizer = BertTokenizer.from_pretrained(config.pretrain_model_path)
        self.vocab = load_vocab(config.vocab_path)
        self.config.vocab_size = len(self.vocab)
        self.sentences = []
        self.load()

    def load_schema(self, path):
        with open(path, encoding="utf8") as f:
            return json.load(f)
    def load(self):
        self.data = []
        with open(self.path, encoding="utf8") as f:
            segments = f.read().split("\n\n")
            for segment in segments:
                sentenece_chars = []
                labels = []
                for line in segment.split("\n"):
                    if line.strip() == "":
                        continue
                    char, label = line.split()
                    sentenece_chars.append(char)
                    labels.append(self.label_to_index[label])
                sentence = "".join(sentenece_chars)
                self.sentences.append(sentence)
                if self.config.model_type == "bert":
                    input_id = self.tokenizer.encode(sentence,
                                                     max_length=self.config.max_length,
                                                     padding="max_length",
                                                     truncation=True)
                else:
                    input_id = self.encode_sentence(sentence)
                input_id = torch.LongTensor(input_id)
                labels=self.padding(labels,-1)
                label_index = torch.LongTensor(labels)
                self.data.append([input_id, label_index])
        return

    def encode_sentence(self, text):
        input_id = []
        for char in text:
            input_id.append(self.vocab.get(char, self.vocab["[UNK]"]))
        input_id = self.padding(input_id)
        return input_id

    #补齐或截断输入的序列，使其可以在一个batch内运算
    def padding(self, input_id, pad_token=0):
        input_id = input_id[:self.config.max_length]
        input_id += [pad_token] * (self.config.max_length - len(input_id))
        return input_id

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):
        return self.data[index]

def load_vocab(vocab_path):
    token_dict = {}
    with open(vocab_path, encoding="utf8") as f:
        for index, line in enumerate(f):
            token = line.strip()
            token_dict[token] = index + 1  #0留给padding位置，所以从1开始
    return token_dict


#用torch自带的DataLoader类封装数据
def load_data(data_path, config, shuffle=True):
    dg = DataGenerator(data_path, config)
    dl = DataLoader(dg, batch_size=config.batch_size, shuffle=shuffle)
    return dl

if __name__ == "__main__":
    from config import Config
    config = Config()
    dg = DataGenerator(config.train_data_path, config)
    print(dg[1])
