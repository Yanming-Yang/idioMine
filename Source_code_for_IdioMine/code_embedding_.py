from transformers import AutoTokenizer, AutoModel
import torch
import pandas as pd
import tensorflow as tf
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score
from skopt import gp_minimize
from skopt.space import Real, Integer
from sklearn.metrics import pairwise_distances_argmin_min

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
    
    space = [Real(0.01, 0.5, name='eps'),
         Integer(2, 10, name='min_samples')]

    result = gp_minimize(objective, space, n_calls=50, random_state=0)

    best_eps, best_min_samples = result.x
    best_score = -result.fun

    print('result', result)
    print('best_eps', best_eps)
    print('best_min_samples', best_min_samples)
    print('best_score', best_score)
    return best_eps, best_min_samples

def get_embedding_pkl(data_file, embedding_file):
    # data_file = r'./code_pattern_str.pkl'
    data = pd.read_pickle(data_file)
    embeddings_data = get_code_embedding(data_file)
    # embedding_file = r'./code_embedding.pkl'
    data.insert(data.shape[1], 'code_embedding', embeddings_data)
    pd.to_pickle(data, embedding_file)

def clustering(embedding_file, cluster_data_file):
    data = pd.read_pickle(embedding_file)
    embedding_data = data['code_embedding']

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
    cluster_labels = perform_best_DBSCAN_and_analysis(embeddings_list, info_list, best_eps, best_min_samples, cluster_data_file)

def perform_best_DBSCAN_and_analysis(data, info_list, best_eps, best_min_samples, cluster_data_file):
    data = np.stack([tensor.numpy() for tensor in data])
    # dbscan = DBSCAN(eps=best_eps, min_samples=best_min_samples)
    dbscan = DBSCAN(eps=best_eps, min_samples=best_min_samples)
    dbscan.fit(data)
    cluster_labels = dbscan.labels_
    # Get unique cluster labels
    unique_labels = set(cluster_labels)
    cluster_data = pd.DataFrame(columns=['label', 'center_point', 'cluster_size', 'center_point_info', 'cluster_data'])
    # Iterate over each unique cluster label
    for label in unique_labels:
        if label == -1:
            # Skip noise points
            continue
        # Get samples that belong to this cluster
        points_in_cluster = data[cluster_labels == label]
        infos = [info_list[i] for i in np.where(cluster_labels == label)[0].tolist()]
        print('infos', infos)
        # Calculate centroid of the cluster
        centroid = np.mean(points_in_cluster, axis=0)
        closest_point_idx, _ = pairwise_distances_argmin_min(points_in_cluster, np.array([centroid]))
        if len(closest_point_idx) > 0 and infos != None:
            closest_point = [infos[idx] for idx in closest_point_idx][0]
            if closest_point != None:
                closest_point_str = closest_point[3]
            else:
                closest_point_str = None
        else:
            closest_point = None
        print(f"Nearest point to center of cluster {label}: {closest_point_str}, and {len(points_in_cluster)}")
        cluster_data.loc[len(cluster_data.index)] = [label, closest_point_str, len(points_in_cluster), infos[closest_point_idx[0]], infos]
        # cluster_data = pd.concat([cluster_data, pd.DataFrame({'label': label, 'center_point': closest_point_str, 'cluster_size': points_in_cluster, 'center_point_info': infos[closest_point_idx[0]]})])
    pd.to_pickle(cluster_data, cluster_data_file)
    print('load data')
    return cluster_labels


