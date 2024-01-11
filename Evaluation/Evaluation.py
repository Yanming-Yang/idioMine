from data_analysis import read_effective_data_in_a_pro
from ast_to_graph import iter_specific_edges
from itertools import chain
import pandas as pd
import argparse
import random
import javalang
import difflib
import Levenshtein
from collections import Counter


def get_code_idioms_in_a_pro(args):
    real_idioms, judges, explaination_idiom, finals = read_effective_data_in_a_pro(args.idiomDataFile)
    code_idioms_list = []
    idx = 0
    for i in range(len(real_idioms)):
        if not (real_idioms[i].count(';') == 1 and ('this.' in real_idioms[i] or 'super.' in real_idioms[i])):
            if not (real_idioms[i].count(';') == 1 and real_idioms[i].count('=') == 0 and real_idioms[i].count('(') == 1):
                if '{' in real_idioms[i] or '?' in real_idioms[i] or  real_idioms[i].count('=') > 0:
                    if not (real_idioms[i].count('=') > 0 and real_idioms[i].split('=')[0].strip().count(' ') == 0):
                        print(idx, real_idioms[i])
                        code_idioms_list.append((real_idioms[i], judges[i], explaination_idiom[i], finals[i]))
                        # print(idx, real_idioms[i] + '\n', judges[i] + '\n')
                        # print(libraries_idiom[i] + '\n', explaination_idiom[i] + '\n')
                        print('*' * 50)
                        idx += 1
    return code_idioms_list

def get_code_idioms_in_a_pro_new(args):
    code_idioms_list = []
    real_idioms_pd = pd.read_csv(args.idiomDataFile)
    real_idioms = real_idioms_pd['idiom']
    finals = real_idioms_pd['final']
    for i in range(len(real_idioms)):
        if type(real_idioms[i]) == str:
            if not (real_idioms[i].count(';') == 1 and real_idioms[i].count('=') == 0):
                code_idioms_list.append((real_idioms[i], finals[i]))
    return code_idioms_list

def split_data_for_evaluation(args):
    data = pd.read_pickle(args.initDataFile)
    func_ast = data['func_ast'][0]
    javaFile = data['javaFile'][0]
    data_init = pd.DataFrame(columns=['func_ast', 'javaFile'])
    for i in range(len(func_ast)):
        for j in range(len(func_ast[i])):
            data_init.loc[len(data_init.index)] = [func_ast[i][j], javaFile[i]]
    
    func_ast_ = data_init['func_ast']
    test_index = random.sample(range(len(func_ast_)), int(len(func_ast_) * 0.3))
    test_data = pd.DataFrame([data_init.loc[i] for i in test_index])
    train_data = pd.DataFrame([data_init.loc[i] for i in range(len(func_ast_)) if i not in test_index])
    pd.to_pickle(test_data, args.testFile)
    pd.to_pickle(train_data, args.trainFile)
    return test_data, train_data

def idiomSetPrecision(args, code_idioms_list, test_data, train_data):
    cluster_data = pd.read_pickle(args.clusterDataFile)
    center_point = cluster_data['center_point']
    cluster_size = cluster_data['cluster_size']
    cluster_info = cluster_data['cluster_data']

    test_func_asts = list(test_data['func_ast'])
    test_file_names = list(test_data['javaFile'])
    test_func_names = [ast.name if isinstance(ast, javalang.tree.MethodDeclaration) else '' for ast in test_func_asts]

    train_func_asts = list(train_data['func_ast'])
    train_file_names = list(train_data['javaFile'])
    train_func_names = [ast.name if isinstance(ast, javalang.tree.MethodDeclaration) else '' for ast in train_func_asts]

    train_flags = []
    test_flags = []
    for i in range(len(code_idioms_list)):
        flag_train = 0
        flag_test = 0
        for j in range(len(center_point)):
            # print(center_point)
            # if Levenshtein.ratio(code_idioms_list[i], center_point[j]) > 0.01:
            if center_point[j] != None and (center_point[j] == code_idioms_list[i][0] or difflib.SequenceMatcher(None, center_point[j], code_idioms_list[i][0]).quick_ratio() >= 0.75):
                file_names = [cluster_info_i[1] for cluster_info_i in cluster_info[j]]
                func_names = [cluster_info_i[2] for cluster_info_i in cluster_info[j]]
                for k in range(len(file_names)):
                    if file_names[k] in train_file_names and flag_train == 0:
                        idx = train_file_names.index(file_names[k])
                        if train_func_names[idx] == func_names[k]:
                            flag_train = 1
                            # print(1, code_idioms_list[i][0])
                            # print(1, center_point[j])
                    if file_names[k] in test_file_names and flag_test == 0:
                        idx = test_file_names.index(file_names[k])
                        if test_func_names[idx] == func_names[k]:
                            flag_test = 1
                            # print(2, code_idioms_list[i][0])
                            # print(2, center_point[j])
        train_flags.append(flag_train)
        test_flags.append(flag_test)

    # print(train_flags)
    # print(test_flags)

    covered_idioms = 0
    uncovered_idioms = 0
    for i in range(len(train_flags)):
        if train_flags[i] == 1 and test_flags[i] == 1:
            covered_idioms += 1
        elif train_flags[i] == 1 and test_flags[i] == 0:
            uncovered_idioms += 1

    idiom_set_precision = float(float(covered_idioms) / float(len([i for i in train_flags if i == 1]) + 1))
    print(idiom_set_precision)
    return idiom_set_precision

def idiomCoverage(args):
    # init data
    init_data = pd.read_pickle(args.initDataFile)
    func_ast = init_data['func_ast'][0]
    javaFile = init_data['javaFile'][0]
    data_init = pd.DataFrame(columns=['func_ast', 'javaFile'])

    for i in range(len(func_ast)):
        for j in range(len(func_ast[i])):
            data_init.loc[len(data_init.index)] = [func_ast[i][j], javaFile[i]]

    code_ast = pd.read_pickle(args.codeContentAST)
    sub_code_pattern = code_ast['sub_code_pattern']
    func_sub_graph = code_ast['func_sub_graph']
    G = code_ast['func_graph'] # G.size()
    code_content = code_ast['func_content']
    real_idioms, judges, libraries_idiom, explaination_idiom = read_effective_data_in_a_pro(args.idiomDataFile)
    # real_idioms_pd = pd.read_csv(args.idiomDataFile)
    # real_idioms = real_idioms_pd['idiom']
    idiom_coverage_rate = 0
    idiom_coverages = []
    idiom_size = []
    combination_idiom_size = []
    for i in range(len(real_idioms)):
        idiom_ast_nodes = []
        G_index = []
        idiom_size_ = []
        for j in range(len(sub_code_pattern)):
            if sub_code_pattern[j] != [] and sub_code_pattern[j] != None:
                for k in range(len(sub_code_pattern[j])):
                    judge = [True if token in real_idioms else False for token in sub_code_pattern[j][k].replace('\{\}', ';').replace('{', ';').replace('}', ';').split(';')] 
                    if type(real_idioms[i]) == str and sub_code_pattern[j][k] in real_idioms[i] or True in judge: # difflib.SequenceMatcher(None, center_point[j], code_idioms_list[i][0]).quick_ratio() > 0.5
                    # if type(real_idioms[i]) == str and difflib.SequenceMatcher(None,sub_code_pattern[j][k], real_idioms[i]).quick_ratio() > 0.75 or False not in judge:
                        if list(set(list(func_sub_graph[j][k]))) != [0] and func_sub_graph[j][k] != []:
                            # print(func_sub_graph[j][k])
                            idiom_ast_nodes.append(func_sub_graph[j][k])
                            G_index.append(j)

        # for k in range(len(code_content)):
        #     if difflib.SequenceMatcher(None, code_content[k], real_idioms[i]).quick_ratio()> 0.5:
        #         combination_idiom_size.append(int(G[k].size()* difflib.SequenceMatcher(None, code_content[k], real_idioms[i]).quick_ratio()))
        keys = list(set(G_index))
        index_result = Counter(G_index)
        index = 0
        idiom_coverage_list = []
        idiom_coverage = 0
        for key in keys:
            value = index_result[key]
            idiom_coverage_ = float(len(list(chain.from_iterable(idiom_ast_nodes[index: index + value]))) / G[key].size())
            index += value
            idiom_coverage_list.append(idiom_coverage_)
            related_leafs = 0
            try:
                node_list = list(chain.from_iterable(idiom_ast_nodes[index: index + value]))
                for i in node_list:
                    related_leafs = get_leaves(node_list, G, key, i, related_leafs)
                    # print('related_leafs', related_leafs)
                    # related_leafs += len(list(iter_specific_edges(G[key], i, 'AST')))
                idiom_size_.append(len(node_list) + related_leafs)
            except:
                continue
            idiom_size_.append(len(node_list) + related_leafs)
        # print(idiom_coverage_list)

        # idiom_coverage = float(sum(idiom_coverage_list) / (len(idiom_coverage_list) + 1))
        idiom_coverage = float(sum(idiom_coverage_list) / (len(idiom_coverage_list)))
        idiom_coverages.append(idiom_coverage)
        idiom_size.append(sum(idiom_size_)/(len(idiom_size_))) #sum(idiom_size_)/len(idiom_size_)
        # idiom_size.append(sum(idiom_size_)/(len(idiom_size_) + 1)) #sum(idiom_size_)/len(idiom_size_)
        idiom_coverages.sort()
        idiom_coverage_rate = idiom_coverages[-1]
    return idiom_coverages, idiom_coverage_rate, idiom_size, combination_idiom_size

def get_leaves(node_list, G, key, i, related_leafs):
        for j in list(iter_specific_edges(G[key], i, 'AST')):
            if j not in node_list:
                related_leafs += len(list(iter_specific_edges(G[key], j, 'AST')))
            else:
                i = j
                get_leaves(node_list, G, key, i, related_leafs)
        return related_leafs




# def CHatGPT_precision(args, test_data, train_data, ChatGPT_idiom):
#     code_ast = pd.read_pickle(args.codeContentAST)
#     code_contents = code_ast['func_content']
#     for i in range(len(code_contents)):

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='args description')
    parser.add_argument('--idiomDataFile', '-iDF', type=str, help='the input file')
    parser.add_argument('--initDataFile', '-inDF', type=str, help='the output file')
    parser.add_argument('--clusterDataFile', '-DF', type=str, help='the output file')
    parser.add_argument('--codeContentAST', '-CCA', type=str, help='the output file')
    parser.add_argument('--testFile', '-teF', type=str, help='the output file')
    parser.add_argument('--trainFile', '-trF', type=str, help='the output file')
    args = parser.parse_args()

    # code_idioms_list = get_code_idioms_in_a_pro_new(args)
    code_idioms_list = get_code_idioms_in_a_pro(args)
    test_data, train_data = split_data_for_evaluation(args)
    # test_data = pd.read_pickle(args.testFile)
    # train_data = pd.read_pickle(args.trainFile)
    idiom_set_precision = idiomSetPrecision(args, code_idioms_list, test_data, train_data)
    idiom_coverages, idiom_coverage_rate, idiom_size, combination_idiom_size = idiomCoverage(args)
    print('ISP:', idiom_set_precision)
    print('IC:', idiom_coverage_rate)
    print('idiom_size', max(idiom_size))

    # total = 0
    # for i in idiom_coverages: 
    #     total += i
    # print("Average coverage of idioms:%f"% (float(total)/float(len(idiom_coverages))))

