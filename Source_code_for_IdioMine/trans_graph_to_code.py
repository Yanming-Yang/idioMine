import javalang
import pandas as pd
import networkx as nx
from typing import List, Tuple
from collections import deque, Counter
import re
import traceback
import difflib
from itertools import chain
from treelib import Tree, Node
from ast_to_graph import iter_specific_edges
from sub_graph_structure import make_a_tree_for_func
from ast_to_graph import get_cfg_edges, add_cfg_to_ast, get_Def_Use_edges, Recursion_get_parents
from codeNode import CodeNode

def trans_sub_graphs_to_code(Gs: List[nx.MultiDiGraph], sub_graphs: List[List[int]], func_contents: List[str]):
    all_code_fragements = []
    for i in range(len(func_contents)):
        try:
            func_stmts, func_tree = make_a_tree_for_func(func_contents[i])
            code_fragements = []
            for j in range(len(sub_graphs[i])):
                try:
                    str_ = trans_sub_graph_to_code(Gs[i], sub_graphs[i][j], func_tree)
                    stmt_list = get_code_fragment_for_each_subG(str_)
                    code_tree = build_struc_to_get_code_fragement(stmt_list)
                    code_fragement_str = traversal_code_tree(code_tree)
                    print(code_fragement_str)
                    code_fragements.append(code_fragement_str)
                except:
                    print('the inner loop')
                    traceback.print_exc()
                    # print('*' * 50)
                    # for node in Gs[i].nodes.data():
                    #     print(node)
                    # print('*' * 50)
                    # print(sub_graphs[i][j])
                    # print('*' * 50)
                    # print(func_tree)
                    # print('*' * 50)
                    # print(func_contents[i])
                    # print('*' * 50)
                    print(i, j)
                    continue
            all_code_fragements.append(code_fragements)
        except:
            print('the outter loop')
            traceback.print_exc()
            all_code_fragements.append(None)
            continue
    return all_code_fragements


def mapping_parent_children_node_to_code(G: nx.MultiDiGraph, ast_node_id: int, label: str, code_node_id: int, func_tree: Tree):
    AST_node_to_code_node = []

    root_children_code = [node.identifier for node in func_tree.all_nodes_itr() if func_tree.parent(node.identifier) != None and func_tree.parent(node.identifier).identifier == code_node_id]
    root_children_AST = [node for node in list(iter_specific_edges(G, ast_node_id, 'AST')) if G.nodes[node]['label'] == label]
    # print('AST node', root_children_AST)
    # print('code node', root_children_code)
    def parent_children_node_to_code(i, j):
        if isinstance(G.nodes[root_children_AST[i]]['code'], javalang.tree.IfStatement):
            # if G.nodes[root_children_AST[i]]['code'].else_statement != None:
            #     AST_node_to_code_node.append((root_children_AST[i], [root_children_code[j], root_children_code[j + 1]]))
            #     j += 2
            if G.nodes[root_children_AST[i]]['code'].else_statement == None:
                AST_node_to_code_node.append((root_children_AST[i], [root_children_code[j]]))
                j += 1
            elif G.nodes[root_children_AST[i]]['code'].else_statement != None:
                node_num = iter_elif_node_num(G, root_children_AST[i], j)
                elif_else_num = node_num - j + 1
                root_children_codes = []
                for k in range(elif_else_num):
                    root_children_codes.append(root_children_code[j + k])
                AST_node_to_code_node.append((root_children_AST[i], root_children_codes))
                j = node_num + 1
        elif isinstance(G.nodes[root_children_AST[i]]['code'], javalang.tree.TryStatement):
            if G.nodes[root_children_AST[i]]['code'].catches != None and G.nodes[root_children_AST[i]]['code'].finally_block != None:
                AST_node_to_code_node.append((root_children_AST[i], [root_children_code[j], root_children_code[j + 1], root_children_code[j + 2]]))
                j += 3
            elif  G.nodes[root_children_AST[i]]['code'].catches != None and G.nodes[root_children_AST[i]]['code'].finally_block == None:
                AST_node_to_code_node.append((root_children_AST[i], [root_children_code[j], root_children_code[j + 1]]))
                j += 2
            elif G.nodes[root_children_AST[i]]['code'].catches == None and G.nodes[root_children_AST[i]]['code'].finally_block != None:
                AST_node_to_code_node.append((root_children_AST[i], [root_children_code[j], root_children_code[j + 1]]))
                j += 2
            elif G.nodes[root_children_AST[i]]['code'].catches == None and G.nodes[root_children_AST[i]]['code'].finally_block == None:
                AST_node_to_code_node.append((root_children_AST[i], [root_children_code[j]]))
                j += 1
        elif isinstance(G.nodes[root_children_AST[i]]['code'], javalang.tree.DoStatement):
            if G.nodes[root_children_AST[i]]['code'].condition != None:
                AST_node_to_code_node.append((root_children_AST[i], [root_children_code[j], root_children_code[j + 1]]))
                j += 2
        elif isinstance(G.nodes[root_children_AST[i]]['code'], javalang.tree.BlockStatement):
            # block_children = list(iter_specific_edges(G, root_children_AST[i], 'AST'))
            # del root_children_AST[i]
            # for child in block_children:
            #     root_children_AST.append(child)
            # parent_children_node_to_code(i, j)  
            root_children_code_ = [node.identifier for node in func_tree.all_nodes_itr() if func_tree.parent(node.identifier) != None and func_tree.parent(node.identifier).identifier == root_children_code[j]]
            AST_node_to_code_node.append((root_children_AST[i], root_children_code_))
            j += 1
        else:
            print('root_children_AST', root_children_AST)
            print('i', i)
            print('root_children_code', root_children_code)
            print('j', j)
            AST_node_to_code_node.append((root_children_AST[i], [root_children_code[j]]))
            j += 1
        i += 1
        return i, j
    
    j = 0
    i = 0
    while i < len(root_children_AST):
        i, j = parent_children_node_to_code(i, j)
    return AST_node_to_code_node


# def mapping_parent_children_node_to_code2(G: nx.MultiDiGraph, ast_node_id: int, code_node_id: List[int], func_tree: Tree):
    AST_node_to_code_node = []

    root_children_code = [node.identifier for node in func_tree.all_nodes_itr() if func_tree.parent(node.identifier) != None and func_tree.parent(node.identifier).identifier == code_node_id]

    root_children_AST = list(iter_specific_edges(G, ast_node_id, 'AST'))

    # for i in range(len(root_children_AST)):

    def parent_children_node_to_code(i, j):
        if not isinstance(G.nodes[root_children_AST[i]]['code'], (javalang.tree.IfStatement, 
                    javalang.tree.TryStatement, javalang.tree.DoStatement, javalang.tree.BlockStatement)):
            AST_node_to_code_node.append((root_children_AST[i], [root_children_code[j]]))
            j += 1
        elif isinstance(G.nodes[root_children_AST[i]]['code'], javalang.tree.IfStatement):
            if G.nodes[root_children_AST[i]]['code'].else_statement != None and not isinstance(G.nodes[root_children_AST[i]]['code'].else_statement, javalang.tree.IfStatement):
                AST_node_to_code_node.append((root_children_AST[i], [root_children_code[j], root_children_code[j + 1]]))
                j += 2
            else:
                AST_node_to_code_node.append((root_children_AST[i], [root_children_code[j]]))
                j += 1
        elif isinstance(G.nodes[root_children_AST[i]]['code'], javalang.tree.TryStatement):
            if G.nodes[root_children_AST[i]]['code'].catches != [] and G.nodes[root_children_AST[i]]['code'].finally_block != []:
                AST_node_to_code_node.append((root_children_AST[i], [root_children_code[j], root_children_code[j + 1], root_children_code[j + 2]]))
                j += 3
            elif  G.nodes[root_children_AST[i]]['code'].catches != [] and G.nodes[root_children_AST[i]]['code'].finally_block == []:
                AST_node_to_code_node.append((root_children_AST[i], [root_children_code[j], root_children_code[j + 1]]))
                j += 2
            elif G.nodes[root_children_AST[i]]['code'].catches == [] and G.nodes[root_children_AST[i]]['code'].finally_block != []:
                AST_node_to_code_node.append((root_children_AST[i], [root_children_code[j], root_children_code[j + 2]]))
                j += 2
            elif G.nodes[root_children_AST[i]]['code'].catches == [] and G.nodes[root_children_AST[i]]['code'].finally_block == []:
                AST_node_to_code_node.append((root_children_AST[i], [root_children_code[j]]))
                j += 1
        elif isinstance(G.nodes[root_children_AST[i]]['code'], javalang.tree.DoStatement):
            if G.nodes[root_children_AST[i]]['code'].condition != None:
                AST_node_to_code_node.append((root_children_AST[i], [root_children_code[j], root_children_code[j + 1]]))
                j += 2
        elif isinstance(G.nodes[root_children_AST[i]]['code'], javalang.tree.BlockStatement):
            block_children = list(iter_specific_edges(G, root_children_AST[i], 'AST'))
            del root_children_AST[i]
            for child in block_children:
                root_children_AST.append(child)
            parent_children_node_to_code(i, j)     
        else:
            AST_node_to_code_node.append((root_children_AST[i], [root_children_code[j]]))
            j += 1
        i += 1
        return i, j
    
    j = 0
    i = 0
    while i < len(root_children_AST):
        i, j = parent_children_node_to_code(i, j)
    return AST_node_to_code_node


def trans_sub_graph_to_code(G: nx.MultiDiGraph, sub_graph: List[int], func_tree: Tree):
    str_s = []
    sub_graph = remove_node_in_sub_G(G, sub_graph)
    sub_graph = deque(sub_graph)
    AST_Children_node_to_code = mapping_parent_children_node_to_code(G, 0,'body', 1, func_tree)
    # if process_sub_G(G, sub_graph):
    if True:
        while len(sub_graph) != 0:
            str_ = ''
            if sub_graph[0] != -1:
                if G.nodes[sub_graph[0]]['label'] != 'body' and G.nodes[sub_graph[0]]['parent'] == 0:
                    sub_graph.popleft()
                    continue
                parent_ids = []
                parent_ids = Recursion_get_parents(G, sub_graph[0], parent_ids)
                if len(parent_ids) == 2:
                    code_ast = [code_node[0] for code_node in  AST_Children_node_to_code]
                    code_str = [code_node[1] for code_node in  AST_Children_node_to_code]
                    index = code_ast.index(parent_ids[0])
                    code_nodes = code_str[index]
                    for i in range(len(code_nodes)):
                        str_ += func_tree[code_nodes[i]].data
                
                elif len(parent_ids) > 2:
                    parent_ids.reverse()
                    i = 1
                    code_asts = [code_node[0] for code_node in AST_Children_node_to_code]
                    code_strs = [code_node[1] for code_node in AST_Children_node_to_code]
                    index = code_asts.index(parent_ids[i])
                    code_str = code_strs[index]

                    str_, AST_Children_node_to_code, i, code_str = process_diff_types_stmts(G, parent_ids, i, AST_Children_node_to_code, code_str, func_tree, str_)
                str_s.append(str_)
                AST_Children_node_to_code = mapping_parent_children_node_to_code(G, 0, 'body', 1, func_tree)
                sub_graph.popleft()
    return str_s

def process_diff_types_stmts(G, parent_ids, i, AST_Children_node_to_code, code_str, func_tree, str_):
    if isinstance(G.nodes[parent_ids[i]]['code'], javalang.tree.IfStatement):
        if G.nodes[parent_ids[i + 1]]['label'] == 'condition':
            str_, code_str, AST_Children_node_to_code, i = process_IfStatement_type_condition(G, parent_ids, i, AST_Children_node_to_code, func_tree, str_)
        elif G.nodes[parent_ids[i + 1]]['label'] == 'then_statement':
            str_, code_str, AST_Children_node_to_code, i = process_IfStatement_type_then(G, parent_ids, i, AST_Children_node_to_code, func_tree, str_)
        elif G.nodes[parent_ids[i + 1]]['label'] == 'else_statement':
            str_, code_str, AST_Children_node_to_code, i = process_IfStatement_type_else(G, parent_ids, i, AST_Children_node_to_code, func_tree,str_)
    elif isinstance(G.nodes[parent_ids[i]]['code'], javalang.tree.TryStatement):
        if G.nodes[parent_ids[i + 1]]['label'] == 'resources':
            str_, code_str, AST_Children_node_to_code, i = process_TryStatement_type_resource(G, parent_ids, i, AST_Children_node_to_code, func_tree, str_)
        elif G.nodes[parent_ids[i + 1]]['label'] == 'block':
            str_, code_str, AST_Children_node_to_code, i = process_TryStatement_type_try(G, parent_ids, i, AST_Children_node_to_code, func_tree, str_)
        elif len(parent_ids) > i + 2 and G.nodes[parent_ids[i + 1]]['label'] == 'catches' and G.nodes[parent_ids[i + 2]]['label'] == 'parameter':
            str_, code_str, AST_Children_node_to_code, i = process_TryStatement_type_catch_para(G, parent_ids, i, AST_Children_node_to_code, func_tree, str_)
        elif G.nodes[parent_ids[i + 1]]['label'] == 'catches' and isinstance(G.nodes[parent_ids[i + 1]]['code'], javalang.tree.CatchClause):
            str_, code_str, AST_Children_node_to_code, i = process_TryStatement_type_catch(G, parent_ids, i, AST_Children_node_to_code, func_tree, str_)
        elif G.nodes[parent_ids[i + 1]]['label'] == 'finally_block':
            str_, code_str, AST_Children_node_to_code, i = process_TryStatement_type_finally(G, parent_ids, i, AST_Children_node_to_code, func_tree, str_)
    elif isinstance(G.nodes[parent_ids[i]]['code'], javalang.tree.DoStatement):
        if G.nodes[parent_ids[i + 1]]['label'] == 'body':
            str_, code_str, AST_Children_node_to_code, i = process_DoStatement_body(G, parent_ids, i, AST_Children_node_to_code, func_tree, str_)
        elif G.nodes[parent_ids[i + 1]]['label'] == 'condition':
            str_, code_str, AST_Children_node_to_code, i = process_DoStatement_condition(G, parent_ids, i, AST_Children_node_to_code, func_tree, str_)
    elif isinstance(G.nodes[parent_ids[i]]['code'], javalang.tree.WhileStatement):
        if G.nodes[parent_ids[i + 1]]['label'] == 'condition':
            str_, code_str, AST_Children_node_to_code, i = process_WhileStatement_condition(G, parent_ids, i, AST_Children_node_to_code, func_tree, str_)
        elif G.nodes[parent_ids[i + 1]]['label'] == 'body':
            str_, code_str, AST_Children_node_to_code, i = process_WhileStatement_body(G, parent_ids, i, AST_Children_node_to_code, func_tree, str_)
    elif isinstance(G.nodes[parent_ids[i]]['code'], javalang.tree.ForStatement):
        if G.nodes[parent_ids[i + 1]]['label'] == 'control':
            str_, code_str, AST_Children_node_to_code, i = process_ForStatement_control(G, parent_ids, i, AST_Children_node_to_code, func_tree, str_)
        elif G.nodes[parent_ids[i + 1]]['label'] == 'body':
            str_, code_str, AST_Children_node_to_code, i = process_ForStatement_body(G, parent_ids, i, AST_Children_node_to_code, func_tree, str_)
    elif isinstance(G.nodes[parent_ids[i]]['code'], javalang.tree.SwitchStatement):
        if len(parent_ids) > i + 1:
            if G.nodes[parent_ids[i + 1]]['label'] == 'expression':
                str_, code_str, AST_Children_node_to_code, i = process_SwitchStatement_expression(G, parent_ids, i, AST_Children_node_to_code, func_tree, str_)
            elif G.nodes[parent_ids[i + 1]]['label'] == 'cases':
                str_, code_str, AST_Children_node_to_code, i = process_SwitchStatement_cases(G, parent_ids, i, AST_Children_node_to_code, func_tree, str_)
        else:
            str_, code_str, AST_Children_node_to_code, i = process_SwitchStatement_expression(G, parent_ids, i, AST_Children_node_to_code, func_tree, str_)
    elif isinstance(G.nodes[parent_ids[i]]['code'], javalang.tree.SynchronizedStatement):
        if G.nodes[parent_ids[i + 1]]['label'] == 'lock':
            str_, code_str, AST_Children_node_to_code, i = process_SynchronizedStatement_lock(G, parent_ids, i, AST_Children_node_to_code, func_tree, str_)
        elif G.nodes[parent_ids[i + 1]]['label'] == 'block':
            str_, code_str, AST_Children_node_to_code, i = process_SynchronizedStatement_block(G, parent_ids, i, AST_Children_node_to_code, func_tree, str_)
    elif isinstance(G.nodes[parent_ids[i]]['code'], (javalang.tree.Statement, javalang.tree.Expression, javalang.tree.Declaration, 
                     javalang.tree.VariableDeclarator)):
        str_, code_str, AST_Children_node_to_code, i = process_normal_statement(G, parent_ids, i, AST_Children_node_to_code, func_tree, str_)
    else:
        i += 1
        print(type(G.nodes[parent_ids[i]]['code']))

    return str_, AST_Children_node_to_code, i, code_str       

def process_IfStatement_type_condition(G, parent_ids, i, AST_Children_node_to_code, func_tree, str_):
    AST_nodes = [node_id_tuple[0] for node_id_tuple in AST_Children_node_to_code]
    code_nodes_ = [node_id_tuple[1] for node_id_tuple in AST_Children_node_to_code]
    code_node_id_ = code_nodes_[AST_nodes.index(parent_ids[i])]
    if '{' in func_tree[code_node_id_[0]].data:
        str_ += func_tree[code_node_id_[0]].data[:func_tree[code_node_id_[0]].data.index('{')] + '{'
    else:
        str_ += func_tree[code_node_id_[0]].data
    i = len(parent_ids)
    return str_, None, AST_Children_node_to_code, i

def process_IfStatement_type_then(G, parent_ids, i, AST_Children_node_to_code, func_tree, str_):
    AST_nodes = [node_id_tuple[0] for node_id_tuple in AST_Children_node_to_code]
    code_nodes_ = [node_id_tuple[1] for node_id_tuple in AST_Children_node_to_code]
    code_node_id_ = code_nodes_[AST_nodes.index(parent_ids[i])]
    # str_ += func_tree[code_node_id_[0]].data[:func_tree[code_node_id_[0]].data.index('{')] + '{'
    if '{' in func_tree[code_node_id_[0]].data:
        str_ += func_tree[code_node_id_[0]].data[:func_tree[code_node_id_[0]].data.index('{')] + '{'
    else:
        str_ += func_tree[code_node_id_[0]].data
    if isinstance(G.nodes[parent_ids[i + 1]]['code'], javalang.tree.BlockStatement):
        index = list(iter_specific_edges(G, parent_ids[i + 1], 'AST')).index(parent_ids[i + 2])
        # print('ast node', parent_ids[i + 1])
        # print('AST_Children_node_to_code', AST_Children_node_to_code)
        # print('code node', code_nodes_)
        AST_Children_node_to_code = mapping_parent_children_node_to_code(G, parent_ids[i + 1], 'statements', code_node_id_[0], func_tree)
        code_str = [code_node[1] for code_node in AST_Children_node_to_code][index]
        if len(parent_ids) > i + 2:
            str_, _, _, _ = process_diff_types_stmts(G, parent_ids, i + 2, AST_Children_node_to_code, code_str, func_tree, str_)
            # str_ += str_i
        else:
            for j in range(len(code_str)):
                str_ += func_tree[code_str[j]].data
            i = len(parent_ids)

    return str_, code_str, AST_Children_node_to_code, i

def process_IfStatement_type_else(G, parent_ids, i, AST_Children_node_to_code, func_tree, str_):
    AST_nodes = [node_id_tuple[0] for node_id_tuple in AST_Children_node_to_code]
    code_nodes_ = [node_id_tuple[1] for node_id_tuple in AST_Children_node_to_code]
    code_node_id_ = code_nodes_[AST_nodes.index(parent_ids[i])]
    if isinstance(G.nodes[parent_ids[i + 1]]['code'], javalang.tree.BlockStatement):
        str_ += func_tree[code_node_id_[0]].data[:func_tree[code_node_id_[0]].data.index('{')] + '{' + '} else {'
        index = [node for node in list(iter_specific_edges(G, parent_ids[i + 1], 'AST')) if G.nodes[node]['label'] == 'statements'].index(parent_ids[i + 2])
        AST_Children_node_to_code = mapping_parent_children_node_to_code(G, parent_ids[i + 1], 'statements', code_node_id_[1], func_tree)
        code_str = [code_node[1] for code_node in AST_Children_node_to_code][index]
        if len(parent_ids) > i + 2:
            str_, _, _, _ = process_diff_types_stmts(G, parent_ids, i + 2, AST_Children_node_to_code, code_str, func_tree, str_)
            # str_ += str_i
        else:
            for j in range(len(code_str)):
                str_ += func_tree[code_str[j]].data 
            i = len(parent_ids)
    elif isinstance(G.nodes[parent_ids[i + 1]]['code'], javalang.tree.IfStatement):
        str_ += func_tree[code_node_id_[0]].data[:func_tree[code_node_id_[0]].data.index('{')] + '{' + '}'  
        code_children = func_tree.children(func_tree.parent(code_node_id_[0]).identifier)
        code_str = [code_children[i + 1].identifier for i in range(len(code_children)) if code_children[i].identifier == code_node_id_[0]][0]
        if isinstance(G.nodes[parent_ids[i + 1]]['code'].else_statement, javalang.tree.IfStatement):
            AST_Children_node_to_code = [(parent_ids[i + 1], [code_str])]
        elif G.nodes[parent_ids[i + 1]]['code'].else_statement != None:
            code_children_1 = func_tree.children(func_tree.parent(code_str).identifier)
            code_str_1 = [code_children[i + 1].identifier for i in range(len(code_children_1)) if code_children[i].identifier == code_str][0]
            AST_Children_node_to_code = [(parent_ids[i + 1], [code_str, code_str_1])]
        elif G.nodes[parent_ids[i + 1]]['code'].else_statement == None:
            AST_Children_node_to_code = [(parent_ids[i + 1], [code_str])]
        if len(parent_ids) > i + 1:
            str_, _, _, _ = process_diff_types_stmts(G,parent_ids, i + 1, AST_Children_node_to_code, code_str, func_tree, str_)
        else:
            for j in range(len(code_str)):
                str_ += func_tree[code_str[j]].data 
            i = len(parent_ids)
    # else:
    #     str_ += func_tree[code_node_id_[0]].data[:func_tree[code_node_id_[0]].data.index('{')] + '{' + '}' + '} else {'
    #     index = [node for node in list(iter_specific_edges(G, parent_ids[i + 1], 'AST'))].index(parent_ids[i + 2])
    #     mapping_parent_children_node_to_code2(G, parent_ids[i + 1], )

    return str_, code_str, AST_Children_node_to_code, i

def process_TryStatement_type_resource(G, parent_ids, i, AST_Children_node_to_code, func_tree, str_):
    AST_nodes = [node_id_tuple[0] for node_id_tuple in AST_Children_node_to_code]
    code_nodes_ = [node_id_tuple[1] for node_id_tuple in AST_Children_node_to_code]
    code_node_id_ = code_nodes_[AST_nodes.index(parent_ids[i])]
    str_ += func_tree[code_node_id_[0]].data[:func_tree[code_node_id_[0]].data.index('{')] + '{'
    i = len(parent_ids)
    return str_, None, AST_Children_node_to_code, i

def process_TryStatement_type_try(G, parent_ids, i, AST_Children_node_to_code, func_tree, str_):
    AST_nodes = [node_id_tuple[0] for node_id_tuple in AST_Children_node_to_code]
    code_nodes_ = [node_id_tuple[1] for node_id_tuple in AST_Children_node_to_code]
    code_node_id_ = code_nodes_[AST_nodes.index(parent_ids[i])]
    str_ += func_tree[code_node_id_[0]].data[:func_tree[code_node_id_[0]].data.index('{')] + '{'
    # stxr_i = ''
    index = [node for node in list(iter_specific_edges(G, parent_ids[i], 'AST')) if G.nodes[node]['label'] == 'block'].index(parent_ids[i + 1])
    AST_Children_node_to_code = mapping_parent_children_node_to_code(G, parent_ids[i], 'block', code_node_id_[0], func_tree)
    code_str = [code_node[1] for code_node in AST_Children_node_to_code][index]
    if len(parent_ids) > i + 1:
        # AST_Children_node_to_code = mapping_parent_children_node_to_code(G, parent_ids[i + 1], code_str[0], func_tree)
        str_, _, _, _ = process_diff_types_stmts(G, parent_ids, i + 1, AST_Children_node_to_code, code_str, func_tree, str_)
        # str_ += str_i
    else:
        for j in range(len(code_str)):
            str_ += func_tree[code_str[j]].data
        i = len(parent_ids)
    return str_, code_str, AST_Children_node_to_code, i

def process_TryStatement_type_catch_para(G, parent_ids, i, AST_Children_node_to_code, func_tree, str_):
    AST_nodes = [node_id_tuple[0] for node_id_tuple in AST_Children_node_to_code]
    code_nodes_ = [node_id_tuple[1] for node_id_tuple in AST_Children_node_to_code]
    code_node_id_ = code_nodes_[AST_nodes.index(parent_ids[i])]
    str_ += func_tree[code_node_id_[0]].data[:func_tree[code_node_id_[0]].data.index('{')] + '{' + '}'
    str_ += func_tree[code_node_id_[1]].data[:func_tree[code_node_id_[1]].data.index('{') + 1]
    i = len(parent_ids)
    return str_, None, AST_Children_node_to_code, i

def process_TryStatement_type_catch(G, parent_ids, i, AST_Children_node_to_code, func_tree, str_):
    AST_nodes = [node_id_tuple[0] for node_id_tuple in AST_Children_node_to_code]
    code_nodes_ = [node_id_tuple[1] for node_id_tuple in AST_Children_node_to_code]
    code_node_id_ = code_nodes_[AST_nodes.index(parent_ids[i])]
    str_ += func_tree[code_node_id_[0]].data[:func_tree[code_node_id_[0]].data.index('{')] + '{' + '}'
    str_ += func_tree[code_node_id_[1]].data[:func_tree[code_node_id_[1]].data.index('{') + 1]
    if isinstance(G.nodes[parent_ids[i + 1]]['code'], javalang.tree.CatchClause):
        index = [node for node in list(iter_specific_edges(G, parent_ids[i + 1], 'AST')) if G.nodes[node]['label'] == 'block'].index(parent_ids[i + 2])
        AST_Children_node_to_code = mapping_parent_children_node_to_code(G, parent_ids[i + 1], 'block', code_node_id_[1], func_tree)
        code_str = [code_node[1] for code_node in AST_Children_node_to_code][index]
        if len(parent_ids) > i + 2:
            str_, _, _, _ = process_diff_types_stmts(G, parent_ids, i + 2, AST_Children_node_to_code, code_str, func_tree, str_)
        else:
            for j in range(len(code_str)):
                str_ += func_tree[code_str[j]].data
            i = len(parent_ids)
    return str_, code_str, AST_Children_node_to_code, i
        
def process_TryStatement_type_finally(G, parent_ids, i, AST_Children_node_to_code, func_tree, str_):
    index_next_step = 1
    AST_nodes = [node_id_tuple[0] for node_id_tuple in AST_Children_node_to_code]
    code_nodes_ = [node_id_tuple[1] for node_id_tuple in AST_Children_node_to_code]
    code_node_id_ = code_nodes_[AST_nodes.index(parent_ids[i])]
    str_ += func_tree[code_node_id_[0]].data[:func_tree[code_node_id_[0]].data.index('{')] + '{' + '}'
    str_ += func_tree[code_node_id_[1]].data[:func_tree[code_node_id_[1]].data.index('{') + 1] + '} finally {'
    index = [node for node in list(iter_specific_edges(G, parent_ids[i], 'AST')) if G.nodes[node]['label'] == 'finally_block'].index(parent_ids[i + 1])
    if len(code_node_id_) == 3:
        AST_Children_node_to_code = mapping_parent_children_node_to_code(G, parent_ids[i], 'finally_block', code_node_id_[2], func_tree)
        index_next_step = 2
    elif len(code_node_id_) == 2:
        AST_Children_node_to_code = mapping_parent_children_node_to_code(G, parent_ids[i], 'finally_block', code_node_id_[1], func_tree)
        index_next_step = 1
    code_str = [code_node[1] for code_node in AST_Children_node_to_code][index]
    if len(parent_ids) > i + 1:
        str_, _, _, _ = process_diff_types_stmts(G, parent_ids, i + 1, AST_Children_node_to_code, code_str, func_tree, str_)
    else:
        for j in range(len(code_str)):
            str_ += func_tree[code_str[j]].data
        i = len(parent_ids)
    return str_, code_str, AST_Children_node_to_code, i

def process_DoStatement_body(G, parent_ids, i, AST_Children_node_to_code, func_tree, str_):
    AST_nodes = [node_id_tuple[0] for node_id_tuple in AST_Children_node_to_code]
    code_nodes_ = [node_id_tuple[1] for node_id_tuple in AST_Children_node_to_code]
    code_node_id_ = code_nodes_[AST_nodes.index(parent_ids[i])]
    str_ += func_tree[code_node_id_[0]].data[:func_tree[code_node_id_[0]].data.index('{')] + '{' 
    if isinstance(G.nodes[parent_ids[i + 1]]['code'], javalang.tree.BlockStatement):
        index = [node for node in list(iter_specific_edges(G, parent_ids[i + 1], 'AST')) if G.nodes[node]['label'] == 'statements'].index(parent_ids[i + 2])
        AST_Children_node_to_code = mapping_parent_children_node_to_code(G, parent_ids[i + 1], 'statements', code_node_id_[0], func_tree)
        code_str = [code_node[1] for code_node in AST_Children_node_to_code][index]
        if len(parent_ids) > i + 2:
            str_, _, _, _ = process_diff_types_stmts(G, parent_ids, i + 2, AST_Children_node_to_code, code_str, func_tree, str_)
        else:
            for j in range(len(code_str)):
                str_ += func_tree[code_str[j]].data
            i = len(parent_ids)
    return str_, code_str, AST_Children_node_to_code, i

def process_DoStatement_condition(G, parent_ids, i, AST_Children_node_to_code, func_tree, str_):
    AST_nodes = [node_id_tuple[0] for node_id_tuple in AST_Children_node_to_code] # list
    code_nodes_ = [node_id_tuple[1] for node_id_tuple in AST_Children_node_to_code] #list[list[int]]
    code_node_id_ = code_nodes_[AST_nodes.index(parent_ids[i])]
    str_ += func_tree[code_node_id_[0]].data[:func_tree[code_node_id_[0]].data.index('{')] + '{' + '}'
    str_ += func_tree[code_node_id_[1]].data
    i = len(parent_ids)
    return str_, None, AST_Children_node_to_code, i

def process_WhileStatement_condition(G, parent_ids, i, AST_Children_node_to_code, func_tree, str_):
    AST_nodes = [node_id_tuple[0] for node_id_tuple in AST_Children_node_to_code]
    code_nodes_ = [node_id_tuple[1] for node_id_tuple in AST_Children_node_to_code]
    code_node_id_ = code_nodes_[AST_nodes.index(parent_ids[i])]
    str_ += func_tree[code_node_id_[0]].data[:func_tree[code_node_id_[0]].data.index('{')] + '{'
    i = len(parent_ids)
    return str_, None, AST_Children_node_to_code, i

def process_WhileStatement_body(G, parent_ids, i, AST_Children_node_to_code, func_tree, str_):
    AST_nodes = [node_id_tuple[0] for node_id_tuple in AST_Children_node_to_code]
    code_nodes_ = [node_id_tuple[1] for node_id_tuple in AST_Children_node_to_code]
    code_node_id_ = code_nodes_[AST_nodes.index(parent_ids[i])]
    str_ += func_tree[code_node_id_[0]].data[:func_tree[code_node_id_[0]].data.index('{')] + '{'
    if isinstance(G.nodes[parent_ids[i + 1]]['code'], javalang.tree.BlockStatement):
        index = [node for node in list(iter_specific_edges(G, parent_ids[i + 1], 'AST')) if G.nodes[node]['label'] == 'statements'].index(parent_ids[i + 2])
        AST_Children_node_to_code = mapping_parent_children_node_to_code(G, parent_ids[i + 1], 'statements', code_node_id_[0], func_tree)
        code_str = [code_node[1] for code_node in AST_Children_node_to_code][index]
        if len(parent_ids) > i + 2:
            str_, _, _, _ = process_diff_types_stmts(G, parent_ids, i + 2, AST_Children_node_to_code, code_str, func_tree, str_)
        else:
            for j in range(len(code_str)):
                str_ += func_tree[code_str[j]].data
            i = len(parent_ids)
    else:
        index = [node for node in list(iter_specific_edges(G, parent_ids[i], 'AST')) if G.nodes[node]['label'] == 'body'].index(parent_ids[i + 1])
        AST_Children_node_to_code = mapping_parent_children_node_to_code(G, parent_ids[i], 'body', code_node_id_[0], func_tree)
        code_str = [code_node[1] for code_node in AST_Children_node_to_code][index]
        if len(parent_ids) > i + 1:
            str_, _, _, _ = process_diff_types_stmts(G, parent_ids, i + 1, AST_Children_node_to_code, code_str, func_tree, str_)
        else:
            for j in range(len(code_str)):
                str_ += func_tree[code_str[j]].data
            i = len(parent_ids)
    return str_, code_str, AST_Children_node_to_code, i

def process_ForStatement_control(G, parent_ids, i, AST_Children_node_to_code, func_tree, str_):
    AST_nodes = [node_id_tuple[0] for node_id_tuple in AST_Children_node_to_code]
    code_nodes_ = [node_id_tuple[1] for node_id_tuple in AST_Children_node_to_code]
    code_node_id_ = code_nodes_[AST_nodes.index(parent_ids[i])]
    str_ += func_tree[code_node_id_[0]].data[:func_tree[code_node_id_[0]].data.index('{')] + '{'
    i = len(parent_ids)
    return str_, None, AST_Children_node_to_code, i

def process_ForStatement_body(G, parent_ids, i, AST_Children_node_to_code, func_tree, str_):
    AST_nodes = [node_id_tuple[0] for node_id_tuple in AST_Children_node_to_code]
    code_nodes_ = [node_id_tuple[1] for node_id_tuple in AST_Children_node_to_code]
    code_node_id_ = code_nodes_[AST_nodes.index(parent_ids[i])]
    str_ += func_tree[code_node_id_[0]].data[:func_tree[code_node_id_[0]].data.index('{')] + '{'
    if isinstance(G.nodes[parent_ids[i + 1]]['code'], javalang.tree.BlockStatement):
        index = [node for node in list(iter_specific_edges(G, parent_ids[i + 1], 'AST')) if G.nodes[node]['label'] == 'statements'].index(parent_ids[i + 2])
        AST_Children_node_to_code = mapping_parent_children_node_to_code(G, parent_ids[i + 1], 'statements', code_node_id_[0], func_tree)
        code_str = [code_node[1] for code_node in AST_Children_node_to_code][index]
        if len(parent_ids) > i + 2:
            # AST_Children_node_to_code = mapping_parent_children_node_to_code(G, parent_ids[i + 2], code_str[1], func_tree)
            str_, _, _, _ = process_diff_types_stmts(G, parent_ids, i + 2, AST_Children_node_to_code, code_str, func_tree, str_)
        else:
            for j in range(len(code_str)):
                str_ += func_tree[code_str[j]].data
            i = len(parent_ids)
    return str_, code_str, AST_Children_node_to_code, i


def process_SwitchStatement_expression(G, parent_ids, i, AST_Children_node_to_code, func_tree, str_):
    AST_nodes = [node_id_tuple[0] for node_id_tuple in AST_Children_node_to_code]
    code_nodes_ = [node_id_tuple[1] for node_id_tuple in AST_Children_node_to_code]
    code_node_id_ = code_nodes_[AST_nodes.index(parent_ids[i])]
    str_ += func_tree[code_node_id_[0]].data[:func_tree[code_node_id_[0]].data.index('{')] + '{'
    i = len(parent_ids)
    return str_, None, AST_Children_node_to_code, i

def process_SwitchStatement_cases(G, parent_ids, i, AST_Children_node_to_code, func_tree, str_):
    AST_nodes = [node_id_tuple[0] for node_id_tuple in AST_Children_node_to_code]
    code_nodes_ = [node_id_tuple[1] for node_id_tuple in AST_Children_node_to_code]
    code_node_id_ = code_nodes_[AST_nodes.index(parent_ids[i])]
    str_ += func_tree[code_node_id_[0]].data[:func_tree[code_node_id_[0]].data.index('{')] + '{'
    index = [node for node in list(iter_specific_edges(G, parent_ids[i], 'AST')) if G.nodes[node]['label'] == 'cases'].index(parent_ids[i + 1])
    code_nodes = mapping_parent_children_node_to_code(G, parent_ids[i], 'cases', code_node_id_[0], func_tree)
    k = 0
    str_tmp = ''
    index_tmp = []
    for j in range(len(code_nodes)):
        if 'case' in func_tree[code_nodes[j][1][0]].data:
            k += 1
        if k == index:
            str_tmp += func_tree[code_nodes[j][1][0]].data
            index_tmp.append(j)
            break

    code_strs = [code_node[1] for code_node in code_nodes][index_tmp[0]]
    if len(parent_ids) > i + 3:
        if G.nodes[parent_ids[i + 2]]['label'] == 'case':
            str_ += str_tmp.split(':')[0] + ':'
        AST_Children_node_to_code = mapping_parent_children_node_to_code(G, parent_ids[i + 2], 'statements', code_strs, func_tree)
        str_, _, _, _ = process_diff_types_stmts(G, parent_ids, i + 3, AST_Children_node_to_code, code_nodes, func_tree, str_)
    else:
        if G.nodes[parent_ids[i + 2]]['label'] == 'case':
            str_ += str_tmp.split(':')[0] + ':'
        elif G.nodes[parent_ids[i + 2]]['label'] == 'statements':
            index_ = [node for node in list(iter_specific_edges(G, parent_ids[i + 1], 'AST')) if G.nodes[node]['label'] == 'statements'].index(parent_ids[i + 2])
            if index_ != 0:
                str_ += str_tmp.split(':')[0] + ':'
            str_ += func_tree[code_nodes[index_tmp[index_]]]
        i = len(parent_ids)
    return str_, code_strs, AST_Children_node_to_code, i

def process_SynchronizedStatement_lock(G, parent_ids, i, AST_Children_node_to_code, func_tree, str_):
    AST_nodes = [node_id_tuple[0] for node_id_tuple in AST_Children_node_to_code]
    code_nodes_ = [node_id_tuple[1] for node_id_tuple in AST_Children_node_to_code]
    code_node_id_ = code_nodes_[AST_nodes.index(parent_ids[i])]
    str_ += func_tree[code_node_id_[0]].data[:func_tree[code_node_id_[0]].data.index('{')] + '{'
    i = len(parent_ids)
    return str_, None, AST_Children_node_to_code, i

def process_SynchronizedStatement_block(G, parent_ids, i, AST_Children_node_to_code, func_tree, str_):
    AST_nodes = [node_id_tuple[0] for node_id_tuple in AST_Children_node_to_code]
    code_nodes_ = [node_id_tuple[1] for node_id_tuple in AST_Children_node_to_code]
    code_node_id_ = code_nodes_[AST_nodes.index(parent_ids[i])]
    str_ += func_tree[code_node_id_[0]].data[:func_tree[code_node_id_[0]].data.index('{')] + '{'
    index = [node for node in list(iter_specific_edges(G, parent_ids[i], 'AST')) if G.nodes[node]['label'] == 'block'].index(parent_ids[i + 1])
    AST_Children_node_to_code = mapping_parent_children_node_to_code(G, parent_ids[i], 'block', code_node_id_[0], func_tree)
    # AST_Children_node_to_code = [code_node[1] for code_node in code_nodes]
    code_str = [code_node[1] for code_node in AST_Children_node_to_code][index]
    if len(parent_ids) > i + 1:
        # AST_Children_node_to_code = mapping_parent_children_node_to_code(G, parent_ids[i + 2], code_str[1], func_tree)
        str_, _, _, _ = process_diff_types_stmts(G, parent_ids, i + 1, AST_Children_node_to_code, code_str, func_tree, str_)
    else:
        for j in range(len(code_str)):
            str_ += func_tree[code_str[j]].data
        i = len(parent_ids)
    return str_, code_str, AST_Children_node_to_code, i

def process_normal_statement(G, parent_ids, i, AST_Children_node_to_code, func_tree, str_):
    parent_nodes = []
    add_str_ = ''
    parent_nodes = Recursion_get_parents(G, parent_ids[i], parent_nodes)
    # for node in parent_nodes:
    #     if isinstance(G.nodes[node]['code'], (javalang.tree.IfStatement, javalang.tree.ForStatement, javalang.tree.WhileStatement, 
    # javalang.tree.TryStatement, javalang.tree.SynchronizedStatement, javalang.tree.SwitchStatement, javalang.tree.DoStatement)):
    #         add_str_ += '}'
    AST_nodes = [node_id_tuple[0] for node_id_tuple in AST_Children_node_to_code]
    code_nodes_ = [node_id_tuple[1] for node_id_tuple in AST_Children_node_to_code]
    code_node_id_ = code_nodes_[AST_nodes.index(parent_ids[i])]
    add_str_ += func_tree[code_node_id_[0]].data 
    str_ += add_str_
    i = len(parent_ids)
    return str_, None, AST_Children_node_to_code, i

def get_code_fragment_for_each_subG(stmt_list: List[str]) -> List[List[str]]:
    code_snip = []
    final_blocks_all = []
    for i in range(len(stmt_list)):
        final_blocks = []
        stmt_blocks = [str_.strip() for str_ in stmt_list[i].split('{') if str_.strip()  != '']
        stmt_blocks = [i + '{' if ';' not in i or ('for' in i and '(' in i and ')' in i and ';' in i) else i for i in stmt_blocks]
        for stmt_block in stmt_blocks:
            if 'for' in stmt_block and '(' in stmt_block and ')' in stmt_block and '{' in stmt_block:
                final_blocks.append(stmt_block) 
            else:
                stmt = stmt_block.split(';')
                for str_ in stmt:
                    if str_.strip() != '' and str_.strip()[len(str_.strip()) - 1] != '{':
                        final_blocks.append(str_.strip() + ';') 
                    elif str_.strip() != '':
                        final_blocks.append(str_.strip())
        final_blocks_all.append(final_blocks)
    return final_blocks_all

def build_struc_to_get_code_fragement(final_blocks_all: List[List[str]]) -> Tree:
    code_tree = Tree()
    rootNode = CodeNode(-1, None, None, None, None, None)
    code_tree.create_node(identifier= -1, tag = -1, parent=None, data=rootNode)
    index = 0
    for i in range(len(final_blocks_all)):
        flag = False
        for node in code_tree.all_nodes_itr():
            if node.data.value == final_blocks_all[i][0]:
                flag = True
                break
        if not flag:
            if final_blocks_all[i][0][len(final_blocks_all[i][0]) - 1] == '{':
                childNode = CodeNode(index, 'leftBlockNode', None, None, -1, final_blocks_all[i][0])
                code_tree.create_node(identifier= index, tag= index, parent= -1, data= childNode)
                index += 1
            elif final_blocks_all[i][0][0] == '}' and final_blocks_all[i][0][len(final_blocks_all[i][0]) - 1] != '{':
                LeftNodes = [node.identifier for node in code_tree.children(code_tree.parent(index).identifier) if node.data.nodeType == 'leftBlockNode' or node.data.nodeType == 'opensBlockNode']
                matchedLeftNode = LeftNodes[len(LeftNodes) - 1]
                childNode = CodeNode(index, 'rightBlockNode', matchedLeftNode, None, -1, final_blocks_all[i][0])
                code_tree.create_node(identifier= index, tag= index, parent= -1, data= childNode)
                code_tree[matchedLeftNode].data.setMatchedRightBlockNode(index)
                index += 1
            elif final_blocks_all[i][0][0] == '}' and final_blocks_all[i][0][len(final_blocks_all[i][0]) - 1] == '{':
                LeftNodes = [node.identifier for node in code_tree.children(code_tree.parent(index).identifier) if node.data.nodeType == 'leftBlockNode' or node.data.nodeType == 'opensBlockNode']
                matchedLeftNode = LeftNodes[len(LeftNodes) - 1]
                childNode = CodeNode(index, 'openBlockNode', matchedLeftNode, None, -1, final_blocks_all[i][0])
                code_tree.create_node(identifier= index, tag= index, parent= -1, data= childNode)
                code_tree[matchedLeftNode].data.setMatchedRightBlockNode(index)
                index += 1
            elif final_blocks_all[i][0][0] != '}' and final_blocks_all[i][0][len(final_blocks_all[i][0]) - 1] == ';':
                childNode = CodeNode(index, 'leafNode', None, None, -1, final_blocks_all[i][0])
                code_tree.create_node(identifier= index, tag= index, parent= -1, data= childNode)
                index += 1
        for j in range(1, len(final_blocks_all[i])):
            flag = False
            for node in code_tree.all_nodes_itr():
                if node.data.value == final_blocks_all[i][j]:
                    flag = True
                    break
            pre_node = [node for node in code_tree.all_nodes_itr() if node.data.value == final_blocks_all[i][j - 1]][0]
            if not flag:
                if 'leftBlockNode' == pre_node.data.nodeType:
                    if final_blocks_all[i][j][0] != '}' and final_blocks_all[i][j][len(final_blocks_all[i][j]) - 1] == '{':
                        if pre_node.data.matchedRightBlockNode == None:
                            childNode = CodeNode(index, 'leftBlockNode', None, None, pre_node.identifier, final_blocks_all[i][j])
                            code_tree.create_node(identifier= index, tag= index, parent= pre_node.identifier, data= childNode)
                            index += 1
                        else:
                            parent_ = code_tree.parent(pre_node.identifier).identifier
                            childNode = CodeNode(index, 'leftBlockNode', None, None, parent_, final_blocks_all[i][j])
                            code_tree.create_node(identifier= index, tag= index, parent= pre_node.identifier, data= childNode)
                            index += 1
                    elif final_blocks_all[i][j][0] == '}' and final_blocks_all[i][j][len(final_blocks_all[i][j]) - 1] != '{':
                        if pre_node.data.matchedRightBlockNode == None:
                            childNode = CodeNode(index, 'rightBlockNode', pre_node.identifier, 
                                        None, code_tree.parent(pre_node.identifier).identifier, final_blocks_all[i][j])
                            code_tree.create_node(identifier= index, tag= index, 
                                        parent= code_tree.parent(pre_node.identifier).identifier, data= childNode)
                            pre_node.data.setMatchedRightBlockNode(index)
                            index += 1
                        else:
                            if code_tree.parent(pre_node.identifier).identifier != -1:
                                parent_= code_tree.parent(code_tree.parent(pre_node.identifier).identifier).identifier
                            else:
                                parent_ = -1
                            LeftNodes = [node.identifier for node in code_tree.children(parent_) if node.data.nodeType 
                                        == 'leftBlockNode' or node.data.nodeType == 'openBlockNode']
                            matchedLeftNode = LeftNodes[len(LeftNodes) - 1]
                            childNode = CodeNode(index, 'rightBlockNode', matchedLeftNode, None, parent_, final_blocks_all[i][j])
                            code_tree.create_node(identifier= index, tag= index, parent= parent_, data= childNode)
                            code_tree[matchedLeftNode].data.setMatchedRightBlockNode(index)
                            index += 1
                    elif final_blocks_all[i][j][0] == '}' and final_blocks_all[i][j][len(final_blocks_all[i][j]) - 1] == '{': # special
                        if pre_node.data.matchedRightBlockNode == None:
                            childNode = CodeNode(index, 'openBlockNode', pre_node.identifier, 
                                        None, code_tree.parent(pre_node.identifier).identifier, final_blocks_all[i][j])
                            code_tree.create_node(identifier= index, tag= index, 
                                        parent= code_tree.parent(pre_node.identifier).identifier, data= childNode)
                            pre_node.data.setMatchedRightBlockNode(index)
                            index += 1
                        else:
                            if code_tree.parent(pre_node.identifier).identifier != -1:
                                parent_= code_tree.parent(code_tree.parent(pre_node.identifier).identifier).identifier
                            else:
                                parent_ = -1
                            LeftNodes = [node.identifier for node in code_tree.children(parent_) if node.data.nodeType 
                                        == 'leftBlockNode' or node.data.nodeType == 'openBlockNode']
                            matchedLeftNode = LeftNodes[len(LeftNodes) - 1]
                            childNode = CodeNode(index, 'openBlockNode', matchedLeftNode, None, parent_, final_blocks_all[i][j])
                            code_tree.create_node(identifier= index, tag= index, parent= parent_, data= childNode)
                            code_tree[matchedLeftNode].data.setMatchedRightBlockNode(index)
                            index += 1
                    elif final_blocks_all[i][j][0] != '}' and final_blocks_all[i][j][len(final_blocks_all[i][j]) - 1] == ';':
                        if pre_node.data.matchedRightBlockNode == None:
                            childNode = CodeNode(index, 'leafNode', None, None, pre_node.identifier, final_blocks_all[i][j])
                            code_tree.create_node(identifier= index, tag= index, parent= pre_node.identifier, data= childNode)
                            index += 1
                        else:
                            childNode = CodeNode(index, 'leafNode', None, None, 
                                        code_tree.parent(pre_node.identifier).identifier, final_blocks_all[i][j])
                            code_tree.create_node(identifier= index, tag= index, parent= 
                                        code_tree.parent(pre_node.identifier).identifier, data= childNode)
                            index += 1
                elif 'rightBlockNode' == pre_node.data.nodeType:
                    if final_blocks_all[i][j][len(final_blocks_all[i][j]) - 1] == '{':
                        childNode = CodeNode(index, 'leftBlockNode', None, None, 
                                    code_tree.parent(pre_node.identifier).identifier, final_blocks_all[i][j])
                        code_tree.create_node(identifier= index, tag= index, parent= 
                                    code_tree.parent(pre_node.identifier).identifier, data= childNode)
                        index += 1
                    elif final_blocks_all[i][j][0] == '}' and final_blocks_all[i][j][len(final_blocks_all[i][j]) - 1] != '{':
                        if code_tree.parent(pre_node.identifier).identifier != -1:
                            parent_ = code_tree.parent(code_tree.parent(pre_node.identifier).identifier).identifier
                        else:
                            parent_ = -1
                        LeftNodes = [node.identifier for node in code_tree.children(parent_) if 
                                    node.data.nodeType == 'leftBlockNode' or node.data.nodeType == 'openBlockNode']
                        matchedLeftNode = LeftNodes[len(LeftNodes) - 1]
                        childNode = CodeNode(index, 'rightBlockNode', matchedLeftNode, None, parent_, final_blocks_all[i][j])
                        code_tree.create_node(identifier= index, tag= index, parent= parent_, data= childNode)
                        code_tree[matchedLeftNode].data.setMatchedRightBlockNode(index)
                        index += 1
                    elif final_blocks_all[i][j][0] == '}' and final_blocks_all[i][j][len(final_blocks_all[i][j]) - 1] == '{': # special
                        if code_tree.parent(pre_node.identifier).identifier != -1:
                            parent_ = code_tree.parent(code_tree.parent(pre_node.identifier).identifier).identifier
                        else:
                            parent_ = -1
                        LeftNodes = [node.identifier for node in code_tree.children(parent_) if 
                                    node.data.nodeType == 'leftBlockNode' or node.data.nodeType == 'openBlockNode']
                        matchedLeftNode = LeftNodes[len(LeftNodes) - 1]
                        childNode = CodeNode(index, 'openBlockNode', matchedLeftNode, None, parent_, final_blocks_all[i][j])
                        code_tree.create_node(identifier= index, tag= index, parent= parent_, data= childNode)
                        code_tree[matchedLeftNode].data.setMatchedRightBlockNode(index)
                        index += 1
                    elif final_blocks_all[i][j][0] != '}' and final_blocks_all[i][j][len(final_blocks_all[i][j]) - 1] == ';':
                        childNode = CodeNode(index, 'leafNode', None, None, 
                                    code_tree.parent(pre_node.identifier).identifier, final_blocks_all[i][j])
                        code_tree.create_node(identifier= index, tag= index, parent= 
                                    code_tree.parent(pre_node.identifier).identifier, data= childNode)
                        index += 1
                elif 'openBlockNode' == pre_node.data.nodeType:
                    if final_blocks_all[i][j][len(final_blocks_all[i][j]) - 1] == '{':
                        if pre_node.data.matchedRightBlockNode == None:
                            childNode = CodeNode(index, 'leftBlockNode', None, None, pre_node.identifier, final_blocks_all[i][j])
                            code_tree.create_node(identifier= index, tag= index, parent= pre_node.identifier, data= childNode)
                            index += 1
                        else:
                            parent_ = code_tree.parent(pre_node.identifier).identifier
                            childNode = CodeNode(index, 'leftBlockNode', None, None, parent_, final_blocks_all[i][j])
                            code_tree.create_node(identifier= index, tag= index, parent= pre_node.identifier, data= childNode)
                            index += 1
                    elif final_blocks_all[i][j][0] == '}' and final_blocks_all[i][j][len(final_blocks_all[i][j]) - 1] != '{':
                        if pre_node.data.matchedRightBlockNode == None:
                            childNode = CodeNode(index, 'rightBlockNode', pre_node.identifier, None, 
                                        code_tree.parent(pre_node.identifier).identifier, final_blocks_all[i][j])
                            code_tree.create_node(identifier= index, tag= index, parent= 
                                        code_tree.parent(pre_node.identifier).identifier, data= childNode)
                            pre_node.data.setMatchedRightBlockNode(index)
                            index += 1
                        else:
                            if code_tree.parent(pre_node.identifier).identifier != -1:
                                parent_= code_tree.parent(code_tree.parent(pre_node.identifier).identifier).identifier
                            else:
                                parent_ = -1
                            LeftNodes = [node.identifier for node in code_tree.children(parent_) if node.data.nodeType == 'leftBlockNode' or node.data.nodeType == 'openBlockNode']
                            matchedLeftNode = LeftNodes[len(LeftNodes) - 1]
                            childNode = CodeNode(index, 'rightBlockNode', matchedLeftNode, None, parent_, final_blocks_all[i][j])
                            code_tree.create_node(identifier= index, tag= index, parent= parent_, data= childNode)
                            code_tree[matchedLeftNode].data.setMatchedRightBlockNode(index)
                            index += 1
                    elif final_blocks_all[i][j][0] == '}' and final_blocks_all[i][j][len(final_blocks_all[i][j]) - 1] == '{': # special
                        if pre_node.data.matchedRightBlockNode == None:
                            childNode = CodeNode(index, 'openBlockNode', pre_node.identifier, None, 
                                        code_tree.parent(pre_node.identifier).identifier, final_blocks_all[i][j])
                            code_tree.create_node(identifier= index, tag= index, parent= 
                                        code_tree.parent(pre_node.identifier).identifier, data= childNode)
                            pre_node.data.setMatchedRightBlockNode(index)
                            index += 1
                        else:
                            if code_tree.parent(pre_node.identifier).identifier != -1:
                                parent_= code_tree.parent(code_tree.parent(pre_node.identifier).identifier).identifier
                            else:
                                parent_ = -1
                            LeftNodes = [node.identifier for node in code_tree.children(parent_) if node.data.nodeType == 'leftBlockNode' or node.data.nodeType == 'openBlockNode']
                            matchedLeftNode = LeftNodes[len(LeftNodes) - 1]
                            childNode = CodeNode(index, 'openBlockNode', matchedLeftNode, None, parent_, final_blocks_all[i][j])
                            code_tree.create_node(identifier= index, tag= index, parent= parent_, data= childNode)
                            code_tree[matchedLeftNode].data.setMatchedRightBlockNode(index)
                            index += 1
                    elif final_blocks_all[i][j][0] != '}' and final_blocks_all[i][j][len(final_blocks_all[i][j]) - 1] == ';':
                        if pre_node.data.matchedRightBlockNode == None:
                            childNode = CodeNode(index, 'leafNode', None, None, pre_node.identifier, final_blocks_all[i][j])
                            code_tree.create_node(identifier= index, tag= index, parent= pre_node.identifier, data= childNode)
                            index += 1
                        else:
                            parent_ = code_tree.parent(pre_node.identifier).identifier
                            childNode = CodeNode(index, 'leafNode', None, None, parent_, final_blocks_all[i][j])
                            code_tree.create_node(identifier= index, tag= index, parent= parent_, data= childNode)
                            index += 1
                elif 'leafNode' == pre_node.data.nodeType:
                    if final_blocks_all[i][j][len(final_blocks_all[i][j]) - 1] == '{':
                        childNode = CodeNode(index, 'leftBlockNode', None, None, code_tree.parent(pre_node.identifier).identifier, final_blocks_all[i][j])
                        code_tree.create_node(identifier= index, tag= index, parent= code_tree.parent(pre_node.identifier).identifier, data= childNode)
                        index += 1
                    elif final_blocks_all[i][j][0] == '}' and final_blocks_all[i][j][len(final_blocks_all[i][j]) - 1] != '{':
                        if code_tree.parent(pre_node.identifier).identifier != -1:
                            parent_= code_tree.parent(code_tree.parent(pre_node.identifier).identifier).identifier
                        else:
                            parent_ = -1
                        LeftNodes = [node.identifier for node in code_tree.children(parent_) if node.data.nodeType == 'leftBlockNode' or node.data.nodeType == 'openBlockNode']
                        matchedLeftNode = LeftNodes[len(LeftNodes) - 1]
                        childNode = CodeNode(index, 'rightBlockNode', matchedLeftNode, None, parent_, final_blocks_all[i][j])
                        code_tree.create_node(identifier= index, tag= index, parent= parent_, data= childNode)
                        code_tree[matchedLeftNode].data.setMatchedRightBlockNode(index)
                        index += 1
                    elif final_blocks_all[i][j][0] == '}' and final_blocks_all[i][j][len(final_blocks_all[i][j]) - 1] == '{': # special
                        if code_tree.parent(pre_node.identifier).identifier != -1:
                            parent_= code_tree.parent(code_tree.parent(pre_node.identifier).identifier).identifier
                        else:
                            parent_ = -1
                        LeftNodes = [node.identifier for node in code_tree.children(parent_) if node.data.nodeType == 'leftBlockNode' or node.data.nodeType == 'openBlockNode']
                        matchedLeftNode = LeftNodes[len(LeftNodes) - 1]
                        childNode = CodeNode(index, 'openBlockNode', matchedLeftNode, None, parent_, final_blocks_all[i][j])
                        code_tree.create_node(identifier= index, tag= index, parent= parent_, data= childNode)
                        code_tree[matchedLeftNode].data.setMatchedRightBlockNode(index)
                        index += 1
                    elif final_blocks_all[i][j][0] != '}' and final_blocks_all[i][j][len(final_blocks_all[i][j]) - 1] == ';':
                        childNode = CodeNode(index, 'leafNode', None, None, code_tree.parent(pre_node.identifier).identifier, final_blocks_all[i][j])
                        code_tree.create_node(identifier= index, tag= index, parent= code_tree.parent(pre_node.identifier).identifier, data= childNode)
                        index += 1
    return code_tree

def traversal_code_tree(code_tree: Tree):
    code_fragement = []
    code_fragement = traversal_code_node(code_tree, code_tree[-1], code_fragement)
    return code_fragement  

def traversal_code_node(code_tree: Tree, code_node: Node, code_fragement: List[str]) -> str:
    code_fragement_str = ''
    node_children  = code_tree.children(code_node.identifier)
    if code_node.identifier != -1:
        code_fragement.append(code_node.data.value)
    if len(node_children) > 0:
        for child in node_children:
            traversal_code_node(code_tree, child, code_fragement)
            if (child.data.nodeType == 'leftBlockNode' or child.data.nodeType == 'openBlockNode') and (child.data.matchedRightBlockNode == None):
                code_fragement[len(code_fragement) - 1] = code_fragement[len(code_fragement) - 1] + '}'
                child.data.setMatchedRightBlockNode(child.identifier)
    for frag in code_fragement:
        code_fragement_str += frag
    return code_fragement_str

# ---------------------------------------------------------------------------------------------
# utils
# ---------------------------------------------------------------------------------------------

def iter_elif_node_num(G: nx.MultiDiGraph, AST_node: int, index: int):
    if G.nodes[AST_node]['code'].else_statement != None and isinstance(G.nodes[AST_node]['code'].else_statement, javalang.tree.IfStatement):
        index += 1
        elif_node = [node for node in list(iter_specific_edges(G, AST_node, 'AST')) if G.nodes[node]['label'] == 'else_statement'][0]
        index = iter_elif_node_num(G, elif_node, index)
    elif G.nodes[AST_node]['code'].else_statement != None and not isinstance(G.nodes[AST_node]['code'].else_statement, javalang.tree.IfStatement):
        index += 1
    elif G.nodes[AST_node]['code'].else_statement == None:
        index = index
    return index


def find_byte_occurrences(s, byte):
    occurrences = []
    i = s.find(byte)
    while i != -1:
        occurrences.append(i)
        i = s.find(byte, i + 1)
    return occurrences

def count_num_position_of_byte(total_str, byte):
    seqMatch = difflib.SequenceMatcher(None, total_str, byte)
    match = seqMatch.get_matching_blocks()
    position = []
    for match_i in match:
        position.append(match_i.a)
    return position

def remove_node_in_sub_G(G: nx.MultiDiGraph, sub_G: List[int]):
    new_sub_G = []
    if -1 in sub_G:
        sub_G.remove(-1)
    # # sub_G = list(filter(lambda x: x == 0, sub_G))
    for node in sub_G: 
        if G.nodes[node]['label'] == 'parameters' and G.nodes[node]['parent'] == 0:
            sub_G.remove(node)
        elif isinstance(G.nodes[node]['code'], javalang.tree.MemberReference):
            sub_G.remove(node)
    sub_G = list(reversed(sub_G))
    if len(sub_G) >= 1:
        if sub_G[0] != 0 and sub_G[0] != -1:
            new_sub_G.append(sub_G[0])
        for i in range(1, len(sub_G)):
            if G.nodes[sub_G[i - 1]]['parent'] != sub_G[i] and sub_G[i] != 0 and sub_G[i] != -1:
                new_sub_G.append(sub_G[i])
    new_sub_G = list(reversed(new_sub_G))
    return new_sub_G

def process_sub_G(G: nx.MultiDiGraph, sub_G: List[int]):
    flag = True
    # if -1 in sub_G:
    #     flag = False
    if len(sub_G) > 1:
        for i in range(1, len(sub_G)):
            if G.nodes[sub_G[i]]['parent'] == sub_G[i - 1]:
                flag = False
                break
    return flag

def add_new_data_column(data, code_fragement_list, data_file):
    data.insert(data.shape[1], 'sub_code_pattern', code_fragement_list)
    pd.to_pickle(data, data_file)


def main():
    all_func_info_path = r'./func_info_data_new_5.pkl'
    func_data = pd.read_pickle(all_func_info_path)

    pro_names = func_data['project_name']
    file_names = func_data['file_name']
    func_names = func_data['func_name']
    func_return_types = func_data['return_type']
    funcs_paras = func_data['func_paras']
    func_contents = func_data['func_content']
    func_graphs = func_data['func_graph']
    func_sub_graphs = func_data['func_sub_graph']

    # for node in func_graphs[1053].nodes.data():
    #     print(node)
    # func_stmts, func_tree = make_a_tree_for_func(func_contents[1053])
    # for node in func_tree.all_nodes_itr():
    #     print(node)

    # print(func_tree)
    # print('*' * 50)
    # print(func_contents[1053])

    # # print(file_names[2])
    # # print(func_names[2])

    
    # print('sub_graphs', func_sub_graphs[1053])
    # print('*' * 20)
    # str_ = trans_sub_graph_to_code(func_graphs[1053], func_sub_graphs[1053][0], func_tree)
    # print('result', str_)
    # # seqMatch = difflib.SequenceMatcher(None, str_[2].strip(), str_[3].strip())
    # # match = seqMatch.get_matching_blocks() 

    # stmt_list = get_code_fragment_for_each_subG(str_)
    # code_tree = build_struc_to_get_code_fragement(stmt_list)
    # print(code_tree)
    # print('*' * 50)
    # code_fragement = traversal_code_tree(code_tree)
    # print(code_fragement)

    all_code_fragements = trans_sub_graphs_to_code(func_graphs, func_sub_graphs, func_contents)

    new_file_path = r'./code_pattern_str_new_5.pkl'
    add_new_data_column(func_data, all_code_fragements, new_file_path)    

if __name__ == '__main__':
    main()