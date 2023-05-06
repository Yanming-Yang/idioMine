from config import treeNodeType, CFGType, DFGDefType_declators, DFGDefType_name, DFGDefType_name_value, DFGType_name, DFGType_member, DFGUseType_arguments, DFGUseType_member_prefix_operators, DFGUseType_expression, DFGUseType_others
from ast_to_graph import get_cfg_edges, add_cfg_to_ast, get_Def_Use_edges, get_dfg_edges, add_dfg_to_ast, construct_ast_graph, iter_specific_edges, Recursion_get_parents
from get_data import GetJavaFile, getASTFunctions, filter_no_func_file, write_data, read_data
import javalang
import pandas as pd
import networkx as nx
from typing import List, Tuple
from collections import deque
import re
import pickle
import datetime
import time
import eventlet
eventlet.monkey_patch()
import argparse 
import traceback

# import sys   
# sys.setrecursionlimit(100000)


def get_sub_graph_in_a_graph(G: nx.MultiDiGraph, dfg_DefUse: List[Tuple[str, List[int], List[int]]]) -> List[List[int]]:
    '''
    This function is used to get nodes of sub-graphs along with DFG and CFG.
    '''
    var_sub_graph = []
    edges = G.edges.data()
    DFG_DefUse_edge = [edge for edge in edges if edge[2]['label'] == 'DFG_DefUse']
    DFG_UseUse_edge = [edge for edge in edges if edge[2]['label'] == 'DFG_UseUse']
    CFG = [edge for edge in edges if edge[2]['label'] == 'CFG']

    defuse_starts = [node[0] for node in DFG_DefUse_edge]
    defuse_ends = [node[1] for node in DFG_DefUse_edge]

    useuse_starts = [node[0] for node in DFG_UseUse_edge]
    useuse_ends = [node[1] for node in DFG_UseUse_edge]

    def get_var_sub_graph(var_def_use: Tuple[str, List[int], List[int]]) -> List[int]:
        var_sub_graph_nodes = []

        var_defs = var_def_use[1]
        var_uses = var_def_use[2]

        vars = var_defs + var_uses

        if var_def_use[2] != []:
            for i in range(len(var_defs)):
                if var_defs[i] != -1:
                    end = var_defs[i]
                    while end in defuse_starts and end in vars:
                        index = defuse_starts.index(end)
                        defuse_start = defuse_starts[index]
                        defuse_end = defuse_ends[index]
                        if defuse_start in vars and defuse_end in vars:
                            if defuse_start not in var_sub_graph_nodes:
                                var_sub_graph_nodes.append(defuse_start)
                            if defuse_end not in var_sub_graph_nodes:
                                var_sub_graph_nodes.append(defuse_end)
                        end = defuse_end
                        while end in useuse_starts and end in vars:
                            index = useuse_starts.index(end)
                            useuse_start = useuse_starts[index]
                            useuse_end = useuse_ends[index]
                            if useuse_start in vars and useuse_end in vars:
                                if useuse_start not in var_sub_graph_nodes:
                                    var_sub_graph_nodes.append(useuse_start)
                                if useuse_end not in var_sub_graph_nodes:
                                    var_sub_graph_nodes.append(useuse_end)
                            end = useuse_end

                    if len(var_sub_graph_nodes) > 0 and end > var_sub_graph_nodes[len(var_sub_graph_nodes) - 1]:
                        var_sub_graph_nodes.append(end)
                else:
                    end = var_uses[0]
                    if end in defuse_ends and end in vars:
                        var_sub_graph_nodes.append(end)
                    while end in useuse_starts and end in vars:
                        index = useuse_starts.index(end)
                        useuse_start = useuse_starts[index]
                        useuse_end = useuse_ends[index]
                        if useuse_start in vars and useuse_end in vars:
                            if useuse_start not in var_sub_graph_nodes:
                                var_sub_graph_nodes.append(useuse_start)
                            if useuse_end not in var_sub_graph_nodes:
                                var_sub_graph_nodes.append(useuse_end)
                        end = useuse_end        
        return var_sub_graph_nodes

    for var_def_use in dfg_DefUse:
        # sub_G = sorted(var_def_use[1] + var_def_use[2])
        # if 0 in sub_G:
        #     sub_G.remove(0)
        var_sub_graph.append(sorted(var_def_use[1] + var_def_use[2]))
    return var_sub_graph

def add_CFG_nodes_in_a_subgragh(G: nx.MultiDiGraph, var_sub_graph: List[List[int]]):
    G_children = list(iter_specific_edges(G, 0, 'AST'))
    body_children = [child for child in G_children if G.nodes[child]['label'] == 'body']
    for var_sub_graph_nodes in var_sub_graph:
        var_sub_graph_nodes_with_CFG = []
        for i in range(len(var_sub_graph_nodes)):
            parents_node_i = []
            parents_node_i = Recursion_get_parents(G, var_sub_graph_nodes[i], parents_node_i)
            if len(parents_node_i) == 2 and 0 in parents_node_i:
                # get the rank of a statement in a function
                index = body_children.index(var_sub_graph_nodes[i])
                var_sub_graph_nodes_with_CFG.append([index])
            # elif len(parents_node_i) > 2:
            #     node_position = []
    

def get_func_info_in_pros(raw_data) -> List[Tuple[str, str, str, str, List[str], int]]:
    '''
    This function is to get basic information about each methods in projects.
    The returned func_info is the parameter of the method ''get_func_content''.
    '''
    projects = raw_data['project']
    java_files_in_pro = raw_data['javaFile']
    func_asts = raw_data['func_ast']
    func_info = []
    for i in range(len(projects)):
        for j in range(len(java_files_in_pro[i])):
            for k in range(len(func_asts[i][j])):
                # if isinstance(func_asts[i][j][k], javalang.tree.MethodDeclaration):
                func_name = func_asts[i][j][k].name
                func_paras = func_asts[i][j][k].parameters
                return_type = func_asts[i][j][k].return_type
                if isinstance(return_type, (javalang.tree.BasicType, javalang.tree.ReferenceType, javalang.tree.VoidClassReference)):
                    return_type_str = return_type.name
                    return_type_str = return_type_str
                else:
                    return_type_str = None
                    return_type_str = None
                para_names = []  
                for para in func_paras:
                    if isinstance(para, (javalang.tree.FormalParameter, javalang.tree.InferredFormalParameter)):
                        para_name = para.name
                        para_names.append(para_name)
                func_info.append((projects[i], java_files_in_pro[i][j], return_type_str, func_name, para_names, i, j, k))
    return func_info

def get_func_content(func_info, raw_data) -> List[List[List[str]]]:
    '''
    This function is used to get the content of functions in projects.
    '''
    projects = raw_data['project']
    java_files_in_pro = raw_data['javaFile']
    func_asts = raw_data['func_ast']
    
    # return_type_info = [func_info_[2] for func_info_ in func_info]
    func_name_info = [func_info_[3] for func_info_ in func_info]
    func_para_info = [func_info_[4] for func_info_ in func_info]

    pro_ids = [func_info_[5] for func_info_ in func_info]
    file_ids = [func_info_[6] for func_info_ in func_info]
    func_ids = [func_info_[7] for func_info_ in func_info]

    func_contents_info = []

    def get_func_content_in_a_file(filename) -> List[str]:
        funcs = []

        for k in range(len(func_name_info)):
            func_str = ''
            dq = deque([])
            signature = ''
            signature_dq = deque([])
            sig_flag = -1
            for line in open(filename, 'r'):
                if func_name_info[k] in line and ';' not in line and '(' in line and ')' in line:
                    signature = line
                    sig_flag = 0

                elif func_name_info[k] in line and ';' not in line and '(' in line and ')' not in line:
                    sig_flag = 1
                    signature_dq.append('(')
                    signature += line
                    continue
                elif sig_flag == 1 and ';' not in line and '(' not in line and ')' not in line:
                    signature += line
                    continue
                elif sig_flag == 1 and ';' not in line and '(' not in line and ')' in line:
                    signature += line
                    signature_dq.pop()
                    sig_flag = 0

                if sig_flag == 0:
                    signature = signature.replace('//', '').replace('/n', '')
                    if len(func_para_info[k]) == 0 and ',' not in signature and '(' in signature and ')' in signature:
                        func_str += signature
                        if '{' in func_str:
                            dq.append('{')
                        sig_flag = 2
                        continue
                    elif  len(func_para_info[k]) == 1 and ',' not in signature and '(' in signature and ')' in signature:
                        para_sig = signature.split('(')[1].split(')')[0]
                        if func_para_info[k][0] in para_sig:
                            func_str += signature
                            if '{' in func_str:
                                dq.append('{')
                            sig_flag = 2
                            continue
                    elif len(func_para_info[k]) > 1 and len(signature.split(',')) == len(func_para_info[k]):
                        flag = [True if func_para_info[k][m] in signature.split(',')[m] else False 
                                    for m in range(len(signature.split(',')))]
                        if flag[0]:
                            func_str += signature
                            if '{' in func_str:
                                dq.append('{')
                        sig_flag = 2
                        continue
                    # else: 
                    #     print(signature)
                    #     print(func_name_info[k])
                    #     print(func_para_info[k])

                if func_str != '' and sig_flag == 2:
                    if '{' in line and '}' not in line:
                        for j in range(len([substr.start() for substr in re.finditer('{', line)])):
                            dq.append('{')
                        func_str += line
                    if '{' in line and '}' in line:
                        func_str += line
                        line_ = line
                        for j in range(len([substr.start() for substr in re.finditer('{', line_)])):
                            dq.append('{')
                        for j in range(len([substr.start() for substr in re.finditer('}', line)])):
                            dq.pop()
                    if '{' not in line and '}' not in line and len(dq) != 0:
                        func_str += line
                    if '}' in line and '{' not in line and len(dq) != 0:
                        func_str += line
                        for j in range(len([substr.start() for substr in re.finditer('}', line)])):
                            dq.pop()
                        if len(dq) == 0:
                            if remove_comments(func_str) not in funcs:
                                funcs.append((func_name_info[k], remove_comments(func_str), pro_ids[k], file_ids[k], func_ids[k]))
                            break
        return funcs

    for i in range(len(projects)):
        for j in range(len(java_files_in_pro[i])):
            try:
                funs_in_a_file = get_func_content_in_a_file(java_files_in_pro[i][j])
                print(java_files_in_pro[i][j])
                func_contents_info.append((projects[i], java_files_in_pro[i][j], funs_in_a_file))
            except:
                continue
    return func_contents_info 
 

def all_func_info(raw_data, func_contents_info) -> List[Tuple[str, str, str, javalang.ast.Node, List[str], str, nx.MultiDiGraph, List[List[int]]]]:
    '''
    This function is used to get all info about each function in projects.
    '''
    func_info_new = []
    func_ASTs = raw_data['func_ast']
    file_names = raw_data['javaFile']
    exist_method = []

    file_name_list = []

    for i in range(len(file_names)):
        for j in range(len(file_names[i])):
            file_name_ = file_names[i][j]
            for k in range(len(func_ASTs[i][j])):
                file_name_list.append((file_name_ + ';' + func_ASTs[i][j][k].name, (i, j, k)))

    for i in range(len(func_contents_info)):
        pro_name = func_contents_info[i][0]
        file_name = func_contents_info[i][1]
        func_content_info = func_contents_info[i][2]
        for j in range(len(func_content_info)):
            timeout = eventlet.Timeout(60)
            try:
                func_name = func_content_info[j][0]
                func_content = func_content_info[j][1]
                project_id = func_content_info[j][2]
                file_id = func_content_info[j][3]
                func_id = func_content_info[j][4]

                for k in range(len(file_name_list)):
                    if file_name + ';' + func_name == file_name_list[k][0]:
                        # with eventlet.Timeout(120, False):
                        index_a = file_name_list[k][1][0]
                        index_b = file_name_list[k][1][1]
                        index_c = file_name_list[k][1][2]
                        func_paras = func_ASTs[index_a][index_b][index_c].parameters
                        return_type = func_ASTs[index_a][index_b][index_c].return_type
                        
                        G, terminals = construct_ast_graph(func_ASTs[index_a][index_b][index_c], treeNodeType)
                        G_new, dfg_DefUse = get_CFG_and_DFG(G) #wrong
                        var_sub_graph = get_sub_graph_in_a_graph(G_new, dfg_DefUse)
                        new_func_info = (pro_name, file_name, func_name, return_type, func_paras, func_content, G_new, var_sub_graph)
                        if (pro_name, file_name, func_name, return_type, func_paras) not in exist_method:
                            func_info_new.append(new_func_info)
                            exist_method.append((pro_name, file_name, func_name, return_type, func_paras))
                        # if k < len(file_name_list) - 1:
                        #     continue 
                        # else:
                        #     print('break')
                        #     break
            except:
                traceback.print_exc()
                if j < len(func_content_info) - 1:
                    continue 
                else:
                    print('break')
                    break
    return func_info_new

# ----------------------------------------------------------------
# utils for constructing sub graphs with CFG and DFG
# ----------------------------------------------------------------

def get_CFG_and_DFG(G: nx.MultiDiGraph) -> nx.MultiDiGraph:
    cfg_edges = get_cfg_edges(G)
    G = add_cfg_to_ast(G, cfg_edges)
    dfg_DefUse = get_Def_Use_edges(G)
    dfg_edges = get_dfg_edges(dfg_DefUse)
    G = add_dfg_to_ast(G, dfg_edges)
    return G, dfg_DefUse

# ----------------------------------------------------------------
# utils for removing comments in functions.s
# ----------------------------------------------------------------

def remove_comments(content):
    out = re.sub(r'/\*.*?\*/', '', content, flags=re.S)
    out = re.sub(r'(//.*)', '', out)
    return out

# ----------------------------------------------------------------
# utils for data
# ----------------------------------------------------------------

def get_func_info_pkl(func_info_new, all_func_info_path):
    pro_names = [func_info[0] for func_info in func_info_new]
    file_names = [func_info[1] for func_info in func_info_new]
    func_names = [func_info[2] for func_info in func_info_new]
    return_types = [func_info[3] for func_info in func_info_new]
    func_paras_ = [func_info[4] for func_info in func_info_new]
    func_contents = [func_info[5] for func_info in func_info_new]
    graphs = [func_info[6] for func_info in func_info_new]
    sub_graphs = [func_info[7] for func_info in func_info_new]

    data_dict = {'project_name': pro_names, 'file_name': file_names, 'func_name': func_names, 
                'return_type': return_types, 'func_paras': func_paras_, 'func_content': func_contents,
                'func_graph': graphs, 'func_sub_graph': sub_graphs}

    data = pd.DataFrame(data_dict)
    pd.to_pickle(data, all_func_info_path)

def main():
    parser = argparse.ArgumentParser(description='args description')
    parser.add_argument('--dataFilePath', '-dFP', help='the input file')
    parser.add_argument('--all_func_info_path', '-afip', help='the output file')
    args = parser.parse_args()
    data = read_data(args.dataFilePath)

    func_info = get_func_info_in_pros(data)
    func_content_info = get_func_content(func_info, data)
    func_info_all = all_func_info(data, func_content_info)
    
    get_func_info_pkl(func_info_all, args.all_func_info_path)

if __name__ == '__main__':
    main()
    