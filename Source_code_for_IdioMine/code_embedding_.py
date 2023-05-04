from transformers import AutoTokenizer, AutoModel
import torch
import pandas as pd
import tensorflow as tf
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score
from skopt import gp_minimize
from skopt.space import Real, Integer
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics import pairwise_distances_argmin_min
import matplotlib.pyplot as plt
import seaborn as sns

def get_code_embedding(data_file):
    # Load the pre-trained tokenizer
    tokenizer = AutoTokenizer.from_pretrained("microsoft/graphcodebert-base")
    # Load the pre-trained model
    model = AutoModel.from_pretrained("microsoft/graphcodebert-base")
    
    data = pd.read_pickle(data_file)
    sub_code_pattern_str = data['sub_code_pattern']
    pro_names = data['project_name']
    file_names = data['file_name']
    func_names = data['func_name']
    # print(sub_code_pattern_str)

    embeddings_data = []
    for file in range(len(sub_code_pattern_str)):
        if sub_code_pattern_str[file] != None:
            embeddings_data_ = []
            for func in range(len(sub_code_pattern_str[file])):
                code = sub_code_pattern_str[file][func]
                tokenized_code = tokenizer.encode(code, max_length=512, truncation=True, padding="max_length", return_tensors="pt")

                with torch.no_grad():
                    # Generate the embeddings
                    model_output = model(tokenized_code)
                    embeddings = model_output.last_hidden_state.mean(dim=1).squeeze()
                    # print(embeddings)
                embeddings_data_.append((pro_names[file], file_names[file], func_names[file], sub_code_pattern_str[file][func], embeddings))
            embeddings_data.append(embeddings_data_)
        else:
            embeddings_data.append(None)
            continue
    return embeddings_data

def dense_clustering(data):
    data = np.stack([tensor.numpy() for tensor in data])

    # Define the objective function to minimize (silhouette score)
    def objective(params):
        eps, min_samples = params
        dbscan = DBSCAN(eps=eps, min_samples=min_samples)
        labels = dbscan.fit_predict(data)
        score = silhouette_score(data, labels)
        # print('labels', labels)
        return -score
    
    space = [Real(0.01, 1, name='eps'),
         Integer(2, 5, name='min_samples')]

    result = gp_minimize(objective, space, n_calls=50, random_state=0)

    best_eps, best_min_samples = result.x
    best_score = -result.fun

    print('result', result)
    print('best_eps', best_eps)
    print('best_min_samples', best_min_samples)
    print('best_score', best_score)
    return best_eps, best_min_samples


def get_embedding_pkl():
    data_file = r'./code_pattern_str.pkl'
    data = pd.read_pickle(data_file)
    embeddings_data = get_code_embedding(data_file)
    embedding_file = r'./code_embedding.pkl'
    data.insert(data.shape[1], 'code_embedding', embeddings_data)
    pd.to_pickle(data, embedding_file)

def clustering(embedding_file):
    data = pd.read_pickle(embedding_file)
    print(data.columns)
    print(len(data['sub_code_pattern'][0]))
    embedding_data = data['code_embedding']
    print(len(embedding_data[0]))
    # print(embedding_data[100])
    # print(embedding_data[1][0][3].shape)

   # max_size = 0
    embeddings_list = []
    info_list = []
    for embeddings in embedding_data:
        if embeddings != None:
            for embedding in embeddings:
                # if embedding[4].shape[0] > max_size:
                #     max_size = embedding[4].shape[0]
                embeddings_list.append(embedding[4])
                info_list.append((embedding[0], embedding[1], embedding[2], embedding[3]))
        else:
            embeddings_list.append(tf.zeros(768))
            info_list.append(None)
    best_eps, best_min_samples = dense_clustering(embeddings_list)
    cluster_labels = perform_best_DBSCAN_and_analysis(embeddings_list, info_list, best_eps, best_min_samples)
    print(cluster_labels)

    # for i in range(len(cluster_labels)):
    #     print(cluster_labels[i])
    #     if cluster_labels[i] == 1:
    #         print(embedding_data[i][0][3])

def perform_best_DBSCAN_and_analysis(data, info_list, best_eps, best_min_samples):
    data = np.stack([tensor.numpy() for tensor in data])
    # dbscan = DBSCAN(eps=best_eps, min_samples=best_min_samples)
    dbscan = DBSCAN(eps=best_eps, min_samples=best_min_samples)
    clusters_ = dbscan.fit(data)
    cluster_labels = dbscan.labels_
    # Get unique cluster labels
    unique_labels = set(cluster_labels)

    # Iterate over each unique cluster label
    for label in unique_labels:
        if label == -1:
            # Skip noise points
            continue
        # Get samples that belong to this cluster
        points_in_cluster = data[cluster_labels == label]
        infos = [info_list[i] for i in np.where(cluster_labels == label)[0].tolist()]
        # print('infos', infos)
        # Calculate centroid of the cluster
        centroid = np.mean(points_in_cluster, axis=0)
        closest_point_idx, _ = pairwise_distances_argmin_min(points_in_cluster, np.array([centroid]))
        # closest_point = points_in_cluster[closest_point_idx]
        if len(closest_point_idx) > 0 and infos != None:
            closest_point = [infos[idx] for idx in closest_point_idx][0]
            if closest_point != None:
                closest_point_str = closest_point[3]
            else:
                closest_point_str = None
        else:
            closest_point = None
        print(f"Nearest point to center of cluster {label}: {closest_point_str}, and {len(points_in_cluster)}")

    # plt.scatter(data[:, 0], data[:, 1], c=cluster_labels, cmap='viridis')
    sns.kdeplot(x=data[:, 0], y=data[:, 1], cmap='viridis', shade=True, bw_method='silverman')
    sns.scatterplot(x=data[:, 0], y=data[:, 1], hue=cluster_labels, palette='rainbow')
    plt.show()

if __name__ == '__main__':
    # get_embedding_pkl()
    embedding_file = r'./code_embedding.pkl'
    clustering(embedding_file)
