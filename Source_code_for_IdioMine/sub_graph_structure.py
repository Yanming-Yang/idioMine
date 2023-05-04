# from config import treeNodeType, CFGType, DFGDefType_declators, DFGDefType_name, DFGDefType_name_value, DFGType_name, DFGType_member, DFGUseType_arguments, DFGUseType_member_prefix_operators, DFGUseType_expression, DFGUseType_others
# from ast_to_graph import get_cfg_edges, add_cfg_to_ast, get_Def_Use_edges, get_dfg_edges, add_dfg_to_ast, construct_ast_graph, iter_specific_edges, Recursion_get_parents
# from get_data import GetJavaFile, getASTFunctions, filter_no_func_file, write_data, read_data
# from sub_graph import
import javalang
import pandas as pd
import networkx as nx
from typing import List, Tuple
from collections import deque
import re
from treelib import Tree, Node
from ast_to_graph import iter_specific_edges

def make_a_tree_for_func(func):
    func_tree = Tree()
    func_stmts = []
    func_tree.create_node(identifier=1, data = 'root', tag = 1)
    func_stmts, func_tree = get_stmts_in_func(func_tree, func, func_stmts)
    return func_stmts, func_tree

# c = 0

def get_stmts_in_func(func_tree: Tree, func: str, func_stmts: List[Tuple[int, str]], node_parent_id: int = 1):
    '''
    This function aims to use a tree structure to represent the source code of a function. (like a AST)
    '''
    # global c
    dq = deque([])
    flag = 0
    block_str = ''
    func = patterns_for_code_block(func)
    index_1s = [substr.start() for substr in re.finditer('{', func)]
    index_2s = [substr.start() for substr in re.finditer('}', func)]
    func = func[index_1s[0] + 1: index_2s[len(index_2s) - 1]]
    # print('test_', func)
    func = add_return_for_stmt(func)
    sub_func_stmts = re.split('\n|\r|\t|\f|\v', func)
    sub_func_stmts = [stmt for stmt in sub_func_stmts if stmt != '']
    # print('test', sub_func_stmts)
    sub_func_stmts = [stmt + '\n' for stmt in sub_func_stmts]
    # call_stack_index = c
    # c = c + 1
    # print('begin', 'call_stack_index:', call_stack_index, 'sub_func_stmts count:', len(sub_func_stmts))
    i = 0
    for stmt in sub_func_stmts:
        i = sub_func_stmts.index(stmt)
        # if '{' not in sub_func_stmts[i] and '}' not in sub_func_stmts[i] and ';' in sub_func_stmts[i] and flag == 0: 
        if '{' not in sub_func_stmts[i] and '}' not in sub_func_stmts[i] and flag == 0: 
            block_str += sub_func_stmts[i]
            end_indexs = get_for_condition(block_str)
            if len(end_indexs) > 0:
                str_ = block_str[: end_indexs[0] + 1]
                func_stmts.append(str_)
                # add node
                index = func_tree.size() + 1
                func_tree.create_node(data= str_, identifier= index, parent=node_parent_id)
                if '{' in str_:
                    func_stmts, func_tree = get_stmts_in_func(func_tree, func, func_stmts, index)
                # block_str = ''
                if len(end_indexs) > 1:
                    # block_str += sub_func_stmts[i]
                    for j in range(1, len(end_indexs)):
                        str_ = block_str[end_indexs[j - 1] + 1: end_indexs[j] + 1]
                        func_stmts.append(str_)
                        index = func_tree.size() + 1
                        # add node
                        func_tree.create_node(data= str_, identifier= index, parent=node_parent_id)
                        if '{' in str_:
                            func_stmts, func_tree = get_stmts_in_func(func_tree, func, func_stmts, index)
                block_str = ''

        elif '{' in sub_func_stmts[i] and '}' not in sub_func_stmts[i]:
            flag = 1
            block_str += sub_func_stmts[i]
            for j in range(len([substr.start() for substr in re.finditer('{', sub_func_stmts[i])])):
                dq.append('{')
        elif '{' in sub_func_stmts[i] and '}' in sub_func_stmts[i]:
            flags = []
            index_1 = [substr.start() for substr in re.finditer('{', sub_func_stmts[i])]
            index_2 = [substr.start() for substr in re.finditer('}', sub_func_stmts[i])]
            indexs = sorted(index_1 + index_2)
            for index in indexs:
                if index in index_1:
                    dq.append('{')
                else:
                    dq.pop()
                if len(dq) == 0:
                    flag = 0
                    block_str += sub_func_stmts[i][: index + 1]
                    func_stmts.append(block_str)
                    index_ = func_tree.size() + 1
                    # add node
                    func_tree.create_node(data= block_str, identifier= index_, parent=node_parent_id)
                    if '{' in block_str:
                        func_stmts, func_tree = get_stmts_in_func(func_tree, block_str, func_stmts, index_)
                    if sub_func_stmts[i][index:] != '':
                        sub_func_stmts.insert(i + 1, sub_func_stmts[i][index + 1:])
                    block_str = ''
                    flags.append(1)
                    break
            if len(flags) == 0:
                block_str += sub_func_stmts[i]
        elif '{' not in sub_func_stmts[i] and '}' not in sub_func_stmts[i] and flag == 1:
            block_str += sub_func_stmts[i]
        elif '{' not in sub_func_stmts[i] and '}' in sub_func_stmts[i] and flag == 1:
            block_str += sub_func_stmts[i]
            for j in range(len([substr.start() for substr in re.finditer('}', sub_func_stmts[i])])):
                dq.pop()
            if len(dq) == 0:
                flag = 0
                s_index = [j for j in [substr.start() for substr in re.finditer('{', block_str)]][0]
                e_indexs = [j for j in [substr.start() for substr in re.finditer('}', block_str)]]
                e_index = e_indexs[len(e_indexs) - 1]
                stmt_indexs = get_for_condition(block_str)
                stmts1 = ''
                stmts2 = ''
                if len(stmt_indexs) == 0:
                    func_stmts.append(block_str)
                    index = func_tree.size() + 1
                    # add node
                    func_tree.create_node(data= block_str, identifier= index, parent=node_parent_id)
                    if '{' in block_str:
                        func_stmts, func_tree = get_stmts_in_func(func_tree, block_str, func_stmts, index)
                elif len(stmt_indexs) == 1:
                    if stmt_indexs[0] < s_index:
                        stmts = block_str[:stmt_indexs[0] + 1]
                        func_stmts.append(stmts)
                        index = func_tree.size() + 1
                        # add node
                        func_tree.create_node(data= stmts, identifier= index, parent=node_parent_id)
                        if '{' in stmts:
                            func_stmts, func_tree = get_stmts_in_func(func_tree, stmts, func_stmts, index)
                        block_str = block_str[stmt_indexs[0] + 1:]
                        func_stmts.append(block_str)
                        index = func_tree.size() + 1
                        # add node
                        func_tree.create_node(data= block_str, identifier= index, parent=node_parent_id)
                        if '{' in block_str:
                            func_stmts, func_tree = get_stmts_in_func(func_tree, block_str, func_stmts, index)
                    elif stmt_indexs[0] > e_index:
                        stmts = block_str[e_index + 1: stmt_indexs[0] + 1]
                        block_str = block_str[:e_index + 1]
                        func_stmts.append(block_str)
                        index = func_tree.size() + 1
                        # add node
                        func_tree.create_node(data= block_str, identifier= index, parent=node_parent_id)
                        if '{' in block_str:
                            func_stmts, func_tree = get_stmts_in_func(func_tree, block_str, func_stmts, index)
                        func_stmts.append(stmts)
                        index = func_tree.size() + 1
                        # add node
                        func_tree.create_node(data= stmts, identifier= index, parent=node_parent_id)
                        if '{' in stmts:
                            func_stmts, func_tree = get_stmts_in_func(func_tree, stmts, func_stmts, index)
                    else:
                        func_stmts.append(block_str)
                        index = func_tree.size() + 1
                        # add node
                        func_tree.create_node(data= block_str, identifier= index, parent=node_parent_id)
                        if '{' in block_str:
                            func_stmts, func_tree = get_stmts_in_func(func_tree, block_str, func_stmts, index)         
                elif len(stmt_indexs) > 1:
                    for j in range(1, len(stmt_indexs)):
                        if stmt_indexs[j - 1] < s_index and  stmt_indexs[j] > s_index:
                            stmts1 = block_str[: stmt_indexs[j - 1] + 1]
                        if stmt_indexs[j - 1] < e_index and stmt_indexs[j] > e_index:
                            stmts2 = block_str[e_index + 1:]  

                    stmts_indexs_ = get_for_condition(stmts1)
                    if len(stmts_indexs_) > 0:
                        func_stmts.append(stmts1[:stmts_indexs_[0] + 1])
                        index = func_tree.size() + 1
                        # add node
                        func_tree.create_node(data= stmts1[:stmts_indexs_[0] + 1], identifier= index, parent=node_parent_id)
                        if '{' in stmts1[:stmts_indexs_[0] + 1]:
                            func_stmts, func_tree = get_stmts_in_func(func_tree, stmts1[:stmts_indexs_[0] + 1], func_stmts, index)
                    if len(stmts_indexs_) > 1:
                        for j in range(1, len(stmts_indexs_)):
                            func_stmts.append(stmts1[stmts_indexs_[j - 1] + 1: stmts_indexs_[j] + 1])
                            index = func_tree.size() + 1
                            # add node
                            func_tree.create_node(data= stmts1[stmts_indexs_[j - 1] + 1: stmts_indexs_[j] + 1], identifier= index, parent=node_parent_id)
                            if '{' in stmts1[stmts_indexs_[j - 1] + 1: stmts_indexs_[j] + 1]:
                                func_stmts, func_tree = get_stmts_in_func(func_tree, stmts1[stmts_indexs_[j - 1] + 1: stmts_indexs_[j] + 1], func_stmts, index)
                    func_stmts.append(block_str.replace(stmts1, '').replace(stmts2, ''))
                    index = func_tree.size() + 1
                    # add node
                    func_tree.create_node(data= block_str.replace(stmts1, '').replace(stmts2, ''), identifier= index, parent=node_parent_id)
                    if '{' in block_str.replace(stmts1, '').replace(stmts2, ''):
                        func_stmts, func_tree = get_stmts_in_func(func_tree, block_str.replace(stmts1, '').replace(stmts2, ''), func_stmts, index)

                    stmts_indexs_2 = get_for_condition(stmts2)
                    # print('16', stmts_indexs_2)
                    if len(stmts_indexs_2) > 0:
                        func_stmts.append(stmts2[:stmts_indexs_2[0] + 1])
                        index = func_tree.size() + 1
                        # add node
                        func_tree.create_node(data= stmts2[:stmts_indexs_2[0] + 1], identifier= index, parent=node_parent_id)
                        if '{' in stmts1[:stmts_indexs_2[0] + 1]:
                            func_stmts, func_tree = get_stmts_in_func(func_tree, stmts1[:stmts_indexs_2[0] + 1], func_stmts, index)
                        if stmts2[stmts_indexs_2[0] + 1:] != '':
                            sub_func_stmts.insert(i + 1, stmts2[stmts_indexs_2[0] + 1:])
                    if len(stmts_indexs_2) > 1:
                        for k in range(len(stmts_indexs_2)):
                            func_stmts.append(stmts2[stmts_indexs_2[k - 1] + 1: stmts_indexs_2[k] + 1])
                            index = func_tree.size() + 1
                            # add node
                            func_tree.create_node(data= stmts2[stmts_indexs_2[k - 1] + 1: stmts_indexs_2[k] + 1], identifier= index, parent=node_parent_id)
                            if '{' in stmts1[stmts_indexs_2[k - 1] + 1: stmts_indexs_2[k] + 1]:
                                func_stmts, func_tree = get_stmts_in_func(func_tree, stmts1[stmts_indexs_2[k - 1] + 1: stmts_indexs_2[k] + 1], func_stmts, index)
                        if stmts2[stmts_indexs_2[len(stmts_indexs_2) - 1] + 1:] != '':
                            sub_func_stmts.insert(i + 1, stmts2[stmts_indexs_2[len(stmts_indexs_2) - 1] + 1:])
                block_str = ''
    return [i for i in func_stmts if i != ''], func_tree

# ----------------------------------------------------------------
# utils for string patterns
# ----------------------------------------------------------------

def add_return_for_stmt(func_stmt):
    index_1 = [substr.start() for substr in re.finditer('\(', func_stmt)]
    index_2 = [substr.start() for substr in re.finditer('\)', func_stmt)]
    index_3s = [substr.start() for substr in re.finditer(';', func_stmt)]
    index_1s, index_2s = process_brackets(index_1, index_2)
    index = 0
    for i in range(len(index_3s)):
        flag = True
        for j in range(len(index_1s)):
            if  index_3s[i] > index_1s[j] and index_3s[i] < index_2s[j]:
                flag = False
                break
        if flag:
            func_stmt = func_stmt[: index_3s[i] + 1 + index] + '\n' + func_stmt[index_3s[i] + 1 + index:]
            index += 1
    return func_stmt

def get_for_condition(func_stmt):
    index_1 = [substr.start() for substr in re.finditer('\(', func_stmt)]
    index_2 = [substr.start() for substr in re.finditer('\)', func_stmt)]
    index_3s = [substr.start() for substr in re.finditer(';', func_stmt)]
    index_1s, index_2s = process_brackets(index_1, index_2)

    index_3s_new = []

    for i in range(len(index_3s)):
        for j in range(len(index_1s)):
            if index_3s[i] > index_1s[j] and index_3s[i] < index_2s[j]:
                index_3s_new.append(index_3s[i])
                break
    return [index for index in index_3s if index not in index_3s_new]
     

def process_brackets(index_1s, index_2s):
    dq = deque([])
    index_1_new = []
    index_2_new = []
    indexs = sorted((index_1s + index_2s))
    for index in indexs:
        if index in index_1s:
            dq.append(index)
        else:
            index_1_new.append(dq.pop())
            index_2_new.append(index)
    return index_1_new, index_2_new


def patterns_for_code_block(func):
    tmp = deque([])
    tmp_index = 0
    index_1s = [substr.start() for substr in re.finditer('\(', func)]
    index_2s = [substr.start() for substr in re.finditer('\)', func)]
    indexs = sorted(index_1s + index_2s)
    for i in range(len(indexs)):
        if indexs[i] in index_1s:
            tmp.append('(')
        if indexs[i] in index_2s:
            tmp.pop()
            if len(tmp) == 0:
                str_ = func[indexs[tmp_index]: indexs[i] + 1].replace('\n','')
                func = func.replace(func[indexs[tmp_index]: indexs[i] + 1], str_)
                tmp_index = i + 1
                continue
    return func

def main():
    all_func_info_path = r'./func_info_data_2.pkl'
    func_data = pd.read_pickle(all_func_info_path)

    pro_names = func_data['project_name']
    file_names = func_data['file_name']
    func_names = func_data['func_name']
    func_return_types = func_data['return_type']
    funcs_paras = func_data['func_paras']
    func_contents = func_data['func_content']
    func_graphs = func_data['func_graph']
    func_sub_graphs = func_data['func_sub_graph']

    func_stmts, func_tree = make_a_tree_for_func(func_contents[1106])
    print(func_tree)
    # print(func_contents[3])
    # for node in func_tree.all_nodes_itr():
    #     print('3', node)
    #     if node.data != '':
    #         # print(node)
    #         print('parent', func_tree.parent(node))

if __name__ == '__main__':
    main()