import pandas as pd
from code_embedding_ import get_code_embedding, clustering


def test_(inputFiles, embedding_file):
    datas = []
    for file in inputFiles:
        data = pd.read_pickle(file)
        embeddings_data = get_code_embedding(file)
        data.insert(data.shape[1], 'code_embedding', embeddings_data)
        datas.append(data)
    data_all = pd.concat(datas)
    print(data_all)
    pd.to_pickle(data, embedding_file)

if __name__ == '__main__':
    # inputFiles = [r'code_pattern_str_new_1.pkl', r'code_pattern_str_new_2.pkl', r'code_pattern_str_new_3.pkl']
    embedding_file = r'code_embedding.pkl'
    # test_(inputFiles, embedding_file)
    clustering(embedding_file)



    # data_file = r'./code_pattern_str.pkl'
    # data = pd.read_pickle(data_file)
    # embeddings_data = get_code_embedding(data_file)
    # embedding_file = r'./code_embedding.pkl'
    # data.insert(data.shape[1], 'code_embedding', embeddings_data)
    # pd.to_pickle(data, embedding_file)



