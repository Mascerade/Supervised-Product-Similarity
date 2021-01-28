import os
import sys
import pandas as pd
import numpy as np
from nltk.corpus import stopwords
from tqdm import tqdm
from transformers import AutoTokenizer
from characterbert_utils.character_cnn import CharacterIndexer
from src.common import Common

# CharacterBERT tokenizer
character_indexer = CharacterIndexer()

# BERT tokenizer
bert_tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")

# ## Data Processsing and Organization
# Here, all we really want to do is prepare the data for training. This includes:
# * Simplifying the original data
# * Normalizing the data 
# * Balancing the positive and negative examples
# * Creating the embedding representations that will actually get fed into the neural network
# Organizing and normalizing the data

def remove_stop_words(phrase):
    '''
    Removes the stop words from a string
    '''

    # Creates the stopwords
    to_stop = stopwords.words('english')
    punctuation = "!”#$%&’()*+,-./:;<=>?@[\]^_`{|}~ "
    for c in punctuation:
        to_stop.append(c)
    to_stop.append('null')
    
    for punc in punctuation:
        phrase = phrase.replace(punc, ' ')
    
    return ' '.join((' '.join([x for x in phrase.split(' ') if x not in to_stop])).split()).lower()

def remove_misc(df):
    '''
    Drop the Unnamed: 0 column and drop any row where it is all NaN
    '''

    df = df.drop(columns=['Unnamed: 0'])
    df = df.dropna(how='all')
    return df

def add_tags(arr):
    '''
    Append the [CLS] and [SEP] tags to a sequence
    '''
    
    return np.char.add(
        np.char.add(
            np.char.add(
                np.char.add(
                    np.array(['[CLS] ']), 
                    arr[:, 0]
                ), 
                np.array([' [SEP] '])
            ), 
            arr[:, 1]
        ), 
        np.array([' [SEP]'])
    )

def character_bert_preprocess_batch(x):
    x = x.astype('U')

    # BERT for title similarity works having the two sentences (sentence1, sentence2)
    # and ordering them in both combinations that they could be (sentence1 + sentence2)
    # and (sentence2 + sentence1). That is why we do np.flip() on x (the input sentences)
    # add_tags just adds the [CLS] and [SEP] tags to the strings
    input1 = add_tags(x)
    input2 = add_tags(np.flip(x, 1))


    # We need to split up each token in the title by the space
    # So, "intel core i7 7700k" becomes ["intel", "core", "i7", "7700k"]
    input1 = np.char.split(input1)
    input2 = np.char.split(input2)

    # Now, we feed the input into the CharacterBERT tokenizer, which converts each 
    input1 = character_indexer.as_padded_tensor(input1)
    input2 = character_indexer.as_padded_tensor(input2)

    return (input1, input2)

def bert_preprocess_batch(x):
    # BERT for title similarity works having the two sentences (sentence1, sentence2)
    # and ordering them in both combinations that they could be (sentence1 + sentence2)
    # and (sentence2 + sentence1). That is why we do np.flip() on x (the input sentences)
    input1 = bert_tokenizer(x.tolist(),
                            return_tensors='pt',
                            padding='max_length',
                            truncation=True,
                            max_length=Common.MAX_LEN)

    input2 = bert_tokenizer(np.flip(x, 1).tolist(),
                            return_tensors='pt',
                            padding='max_length',
                            truncation=True,
                            max_length=Common.MAX_LEN)

    return (input1, input2)