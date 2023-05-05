import pandas as pd
from code_embedding import get_code_embedding, clustering
import traceback

def test_(inputFiles, embedding_file):
    datas = []
    for file in inputFiles:
        data = pd.read_pickle(file)
        embeddings_data = get_code_embedding(file)
        data.insert(data.shape[1], 'code_embedding', embeddings_data)
        datas.append(data)
    data_all = pd.concat(datas)
    print(data_all)
    pd.to_pickle(data_all, embedding_file)

def test__(inputFiles, embedding_files):
    for i in range(len(inputFiles)):
        try:
            data = pd.read_pickle(inputFiles[i])
            embeddings_data = get_code_embedding(inputFiles[i])
            data.insert(data.shape[1], 'code_embedding', embeddings_data)

            pd.to_pickle(data, embedding_files[i])
            print('done_test', i)
        except:
            traceback.print_exc()
            continue

if __name__ == '__main__':
    inputFiles = [
        # r'code_pattern_str_new_8.pkl', r'code_pattern_lib_1.pkl', r'code_pattern_lib_11.pkl'
        r'code_pattern_lib_5_new.pkl'
            ]
    
    # embedding_file = r'code_embedding_all.pkl'
    # cluster_data_file = r'cluster_data_all.pkl'
    # test_(inputFiles, embedding_file)
    # clustering(embedding_file, cluster_data_file)

    embedding_files = [
        r'code_embedding_lib_5_new.pkl'
        # r'code_embedding_8.pkl', r'code_embedding_lib_1_.pkl', r'code_embedding_lib_11_.pkl'
        # r'code_embedding_lib_2_.pkl', r'code_embedding_lib_3_.pkl', r'code_embedding_lib_4_.pkl', r'code_embedding_lib_5_.pkl',
        # r'code_embedding_lib_6_.pkl', r'code_embedding_lib_8_.pkl', r'code_embedding_lib_9_.pkl', r'code_embedding_lib_10_.pkl',
        # r'code_embedding_lib_12_.pkl', r'code_embedding_lib_13_.pkl', r'code_embedding_lib_14_.pkl', r'code_embedding_lib_15_.pkl'
            ]

    test__(inputFiles, embedding_files)

    cluster_data_files = [
        r'cluster_lib_5_all_new.pkl'
        # r'cluster_data_8_all.pkl', r'cluster_lib_1_all.pkl', r'cluster_lib_11_all.pkl'
        # r'cluster_lib_2_all.pkl',  r'cluster_lib_3_all.pkl',  r'cluster_lib_4_all.pkl',  r'cluster_lib_5_all.pkl',
        # r'cluster_lib_6_all.pkl',  r'cluster_lib_8_all.pkl',  r'cluster_lib_9_all.pkl',  r'cluster_lib_10_all.pkl', 
        # r'cluster_lib_12_all.pkl',  r'cluster_lib_13_all.pkl',  r'cluster_lib_14_all.pkl',  r'cluster_lib_15_all.pkl'
    ]

    for i in range(len(embedding_files)):
        try:
            clustering(embedding_files[i], cluster_data_files[i])
            print('done_cluster', i)
        except:

            traceback.print_exc()
            continue



