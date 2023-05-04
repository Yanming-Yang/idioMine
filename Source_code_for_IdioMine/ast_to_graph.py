from get_data import GetJavaFile, getASTFunctions, filter_no_func_file, write_data, read_data
import pandas as pd 
import javalang
import os
import networkx as nx
from typing import List, Tuple, Iterable, Optional, Dict
from matplotlib import pyplot as plt
import ast
from config import treeNodeType, CFGType, DFGDefType_declators, DFGDefType_name, DFGDefType_name_value, DFGType_name, DFGType_member, DFGUseType_arguments, DFGUseType_member_prefix_operators, DFGUseType_expression, DFGUseType_others
from collections import Counter
import re
# import sys   
# sys.setrecursionlimit(100000)


class FuncASTGraph:
    """
    Return an ast in the graph format using networkx.
    Return:
        ast_graph: nx.MultiDiGraph
    """


    def __init__(self, funcAST, G) -> None:
        self.funcAST = funcAST
        self.G = G

def construct_ast_graph(funcAST: javalang.ast.Node, treeNodeType: list):
    G = nx.MultiDiGraph()
    current_node_ID = 0

    def traverse_ast(current_node:javalang.ast.Node) -> nx.MultiDiGraph:
        """Traverse the ast tree to create a directed multi-graph"""
        nonlocal current_node_ID
        if isinstance(current_node, javalang.tree.MethodDeclaration):
            G.add_node(current_node_ID, color='black', code=current_node,
                        label=type(current_node), parent = -1)
        parent_id = current_node_ID
        if isinstance(current_node, treeNodeType) and len(current_node.children) > 0:
            for i in range(len(current_node.children)):
                if 'documentation' in current_node.attrs and current_node.children[i] == current_node.documentation:
                    continue
                if isinstance(current_node.children[i], javalang.ast.Node):
                    current_node_ID += 1
                    G.add_node(current_node_ID, color='pink', code=current_node.children[i], 
                                label=current_node.attrs[i], parent=parent_id)
                    G.add_edge(parent_id, current_node_ID, label='AST')
                    traverse_ast(current_node.children[i])
                elif isinstance(current_node.children[i], list) and len(current_node.children[i]) > 0:
                    for j in range(len(current_node.children[i])):
                        current_node_ID += 1
                        G.add_node(current_node_ID, color='pink', code=current_node.children[i][j], 
                            label=current_node.attrs[i], parent=parent_id)
                        G.add_edge(parent_id, current_node_ID, label='AST')
                        traverse_ast(current_node.children[i][j]) 

    def get_terminals(G: nx.MultiDiGraph) -> List[int]:
        nodes = G.nodes.data()
        parents = [node[1]['parent'] for node in nodes]
        terminals = [i for i in range(len(G.nodes.data())) if i not in parents]
        for terminal in terminals:
            G.nodes[terminal]['color'] = 'red'
        return terminals

    traverse_ast(funcAST)
    
    return G, get_terminals(G)

# ----------------------------------------------------------------
# add CFG to ASTGraph
# def get_cfg_edges: get all cfg edges for a function
# def add_cfg_to_ast: add cfg edges of a method to its ast graph
# ---------------------------------------------------------------
def get_cfg_edges(G: nx.MultiDiGraph):

    cfg_edges = []

    def judge_node_types(node):
        # try:
            if isinstance(node[1]['code'], javalang.tree.IfStatement):
                get_IfStmt_cfg_edges(node)
            elif isinstance(node[1]['code'], javalang.tree.ForStatement):
                get_ForStmt_cfg_edges(node)
            elif isinstance(node[1]['code'], javalang.tree.WhileStatement):
                get_WhileStmt_cfg_edges(node)
            elif isinstance(node[1]['code'], javalang.tree.DoStatement):
                get_DoWhile_cfg_edges(node)
            elif isinstance(node[1]['code'], javalang.tree.BreakStatement):
                get_Break_cfg_edges(node)
            elif isinstance(node[1]['code'], javalang.tree.ContinueStatement):
                get_Continue_cfg_edges(node)
            elif isinstance(node[1]['code'], javalang.tree.SwitchStatement):
                get_Switch_cfg_edges(node)
            elif isinstance(node[1]['code'], javalang.tree.TryStatement):
                get_try_catch_finally_block(node)
            elif isinstance(node[1]['code'], javalang.tree.SynchronizedStatement):
                get_synchronized_cfg_edges(node)
        # except:
        #     return cfg_edges

   

    def get_IfStmt_cfg_edges(current_node: javalang.ast.Node) -> List[Tuple[int, int, str]]:
        '''
        This method is used to build the CFG's edges for the If statement.
        '''
        # node_id: int, node_attr : dict = {'color':, 'code':, 'label':, 'parent': }
            # attributes in IfStatement: condition, then_statement, (else_statement)
        node_id = current_node[0]
        node_attr = current_node[1]
        try:
            if isinstance(node_attr['code'], javalang.tree.IfStatement):
                if_children = list(iter_specific_edges(G, node_id, 'AST'))
                ifParent_children = sorted(list(iter_specific_edges(G, G.nodes[node_id]['parent'], 'AST')))
                condition_child = [child_id for child_id in if_children if G.nodes[child_id]['label'] == 'condition'][0]
                then_child = [child_id for child_id in if_children if G.nodes[child_id]['label'] == 'then_statement'][0]
                cfg_edges.append((node_id, condition_child, 'CFG'))
                then_stmts = list(iter_specific_edges(G, then_child, 'AST'))
                # parent for then_statement and else_statement
                if len(if_children) == 3 and dict(Counter([G.nodes[child]['label'] for child in if_children])) == dict(Counter(['condition', 'then_statement', 'else_statement'])):
                    else_child = [child_id for child_id in if_children if G.nodes[child_id]['label'] == 'else_statement'][0]
                    # two possilbe successors for IfStatement 
                    else_stmts = list(iter_specific_edges(G, else_child, 'AST'))
                    cfg_edges.append((condition_child, then_child, 'CFG'))
                    judge_node_types((then_child, G.nodes[then_child]))
                    if len(then_stmts) > 0:
                        then_child_stmt_ID = min(list(iter_specific_edges(G, then_child, 'AST')))
                        cfg_edges.append((then_child, then_child_stmt_ID, 'CFG'))
                        judge_node_types((then_child_stmt_ID, G.nodes[then_child_stmt_ID]))
                    if len(then_stmts) > 1:
                        for i in range(1, len(then_stmts)):
                            cfg_edges.append((then_stmts[i - 1], then_stmts[i], 'CFG'))
                            judge_node_types((then_stmts[i], G.nodes[then_stmts[i]]))
                    cfg_edges.append((condition_child, else_child, 'CFG'))
                    if len(else_stmts) > 0:
                        cfg_edges.append((else_child, else_stmts[0], 'CFG'))
                        judge_node_types((else_stmts[0], G.nodes[else_stmts[0]])) 
                    if len(else_stmts) > 1:
                        for i in range(1, len(else_stmts)):
                            cfg_edges.append((else_stmts[i - 1], else_stmts[i], 'CFG'))  
                            judge_node_types((else_stmts[i], G.nodes[else_stmts[i]]))      
                    if max(ifParent_children) > node_id:
                        OutIfStmt = ifParent_children[ifParent_children.index(node_id) + 1]
                        if len(list(iter_specific_edges(G, then_child, 'AST'))) > 0:
                            then_child_FinalStmt_ID = max(list(iter_specific_edges(G, then_child, 'AST')))
                            cfg_edges.append((then_child_FinalStmt_ID, OutIfStmt, 'CFG'))
                        else:
                            cfg_edges.append((then_child, OutIfStmt, 'CFG'))

                        if len(list(iter_specific_edges(G, else_child, 'AST'))) > 0:
                            else_child_FinalStmt_ID = max(list(iter_specific_edges(G, else_child, 'AST')))
                            cfg_edges.append((else_child_FinalStmt_ID, OutIfStmt, 'CFG'))
                        else:
                            cfg_edges.append((else_child, OutIfStmt, 'CFG'))
                        
                # no else
                elif len(if_children) == 2 and dict(Counter([G.nodes[child]['label'] for child in if_children])) == dict(Counter(['condition', 'then_statement'])):
                    cfg_edges.append((condition_child, then_child, 'CFG'))
                    judge_node_types((then_child, G.nodes[then_child]))
                    if len(then_stmts) > 0:
                        then_child_stmt_ID = min(list(iter_specific_edges(G, then_child, 'AST')))
                        cfg_edges.append((then_child, then_child_stmt_ID, 'CFG'))
                        judge_node_types((then_child_stmt_ID, G.nodes[then_child_stmt_ID]))
                    if len(then_stmts) > 1:
                        for i in range(1, len(then_stmts)):
                            cfg_edges.append((then_stmts[i - 1], then_stmts[i], 'CFG'))
                            judge_node_types((then_stmts[i], G.nodes[then_stmts[i]]))
                    if max(ifParent_children) > node_id:
                        OutIfStmt = ifParent_children[ifParent_children.index(node_id) + 1]
                        if len(list(iter_specific_edges(G, then_child, 'AST'))) > 0:
                            then_child_FinalStmt_ID = max(list(iter_specific_edges(G, then_child, 'AST')))
                        else:
                            then_child_FinalStmt_ID = condition_child
                        cfg_edges.append((then_child_FinalStmt_ID, OutIfStmt, 'CFG'))
                        cfg_edges.append((condition_child, OutIfStmt, 'CFG'))
        except:
            return cfg_edges
        return cfg_edges

    def get_WhileStmt_cfg_edges(current_node: javalang.ast.Node) -> List[Tuple[int, int, str]]:
        node_id = current_node[0]
        node_attr = current_node[1]
        try:
            if isinstance(node_attr['code'], javalang.tree.WhileStatement):
                while_children = list(iter_specific_edges(G, node_id, 'AST'))
                condition_child = [child_id for child_id in while_children if G.nodes[child_id]['label'] == 'condition'][0]
                body_child = [child_id for child_id in while_children if G.nodes[child_id]['label'] == 'body'][0]
                body_child_stmts = list(iter_specific_edges(G, body_child, 'AST'))
                cfg_edges.append((node_id, condition_child, 'CFG'))
                if len(body_child_stmts) > 0:
                    body_child_stmt_ID = min(body_child_stmts)
                    body_child_final_stmt_ID = max(body_child_stmts)
                    cfg_edges.append((condition_child, body_child_stmt_ID, 'CFG'))
                    judge_node_types((body_child_stmt_ID, G.nodes[body_child_stmt_ID]))
                    cfg_edges.append((body_child_final_stmt_ID, condition_child, 'CFG'))
                    if len(body_child_stmts) > 1:
                        for i in range(1, len(body_child_stmts)):
                            cfg_edges.append((body_child_stmts[i - 1], body_child_stmts[i], 'CFG'))
                            judge_node_types((body_child_stmts[i], G.nodes[body_child_stmts[i]]))
                ifParent_children = sorted(list(iter_specific_edges(G, G.nodes[node_id]['parent'], 'AST')))
                if max(ifParent_children) > node_id:
                    OutIfStmt = ifParent_children[ifParent_children.index(node_id) + 1]
                    cfg_edges.append((condition_child, OutIfStmt, 'CFG'))
        except:
            return cfg_edges
        return cfg_edges

    def get_ForStmt_cfg_edges(current_node: javalang.ast.Node) -> List[Tuple[int, int, str]]:
        node_id = current_node[0]
        node_attr = current_node[1]
        try:
            if isinstance(node_attr['code'], javalang.tree.ForStatement):
                for_children = list(iter_specific_edges(G, node_id, 'AST'))
                control_child = [child_id for child_id in for_children if G.nodes[child_id]['label'] == 'control'][0]
                body_child = [child_id for child_id in for_children if G.nodes[child_id]['label'] == 'body'][0]
                body_child_stmts = sorted(list(iter_specific_edges(G, body_child, 'AST')))
                cfg_edges.append((node_id, control_child, 'CFG'))
                if len(body_child_stmts) > 0:
                    body_child_stmt_ID = min(body_child_stmts)
                    body_child_final_stmt_ID = max(body_child_stmts)
                    cfg_edges.append((body_child_final_stmt_ID, control_child, 'CFG'))
                    cfg_edges.append((control_child, body_child_stmt_ID, 'CFG'))
                    judge_node_types((body_child_stmt_ID, G.nodes[body_child_stmt_ID]))
                    if len(body_child_stmts) > 1:
                        for i in range(1, len(body_child_stmts)):
                            cfg_edges.append((body_child_stmts[i - 1], body_child_stmts[i], 'CFG')) 
                            judge_node_types((body_child_stmts[i], G.nodes[body_child_stmts[i]]))
                ifParent_children = sorted(list(iter_specific_edges(G, G.nodes[node_id]['parent'], 'AST')))
                if max(ifParent_children) > node_id:
                    OutIfStmt = ifParent_children[ifParent_children.index(node_id) + 1]
                    cfg_edges.append((control_child, OutIfStmt, 'CFG'))
        except:
            return cfg_edges
        return cfg_edges

    def get_DoWhile_cfg_edges(current_node: javalang.ast.Node) -> List[Tuple[int, int, str]]:
        node_id = current_node[0]
        node_attr = current_node[1]
        try:
            if isinstance(node_attr['code'], javalang.tree.DoStatement):
                do_children = list(iter_specific_edges(G, node_id, 'AST'))
                condition_child = [child_id for child_id in do_children if G.nodes[child_id]['label'] == 'condition'][0]
                body_child = [child_id for child_id in do_children if G.nodes[child_id]['label'] == 'body'][0]
                body_child_stmts = list(iter_specific_edges(G, body_child, 'AST'))
                body_child_stmt_ID = min(body_child_stmts)
                body_child_final_stmt_ID = max(body_child_stmts)
                ifParent_children = sorted(list(iter_specific_edges(G, G.nodes[node_id]['parent'], 'AST')))
                cfg_edges.append((node_id, body_child, 'CFG'))
                judge_node_types((body_child, G.nodes[body_child]))
                cfg_edges.append((body_child, body_child_stmt_ID, 'CFG'))
                judge_node_types((body_child_stmt_ID, G.nodes[body_child_stmt_ID]))
                cfg_edges.append((condition_child, body_child, 'CFG'))
                if len(body_child_stmts) > 1:
                    cfg_edges.append((body_child_final_stmt_ID, condition_child, 'CFG'))
                    judge_node_types((body_child_final_stmt_ID, G.nodes[body_child_final_stmt_ID]))
                    for i in range(1, len(body_child_stmts)):
                        cfg_edges.append((body_child_stmts[i - 1], body_child_stmts[i], 'CFG'))
                        judge_node_types((body_child_stmts[i], G.nodes[body_child_stmts[i]]))  
                    cfg_edges.append((body_child_stmts[len(body_child_stmts) - 1], condition_child, 'CFG'))           
                if max(ifParent_children) > node_id:
                    OutIfStmt = ifParent_children[ifParent_children.index(node_id) + 1]
                    cfg_edges.append((condition_child, OutIfStmt, 'CFG'))
        except:
            return cfg_edges
        return cfg_edges

    def get_Switch_cfg_edges(current_node: javalang.ast.Node) -> List[Tuple[int, int, str]]:
        node_id = current_node[0]
        node_attr = current_node[1]
        try:
            if isinstance(node_attr['code'], javalang.tree.SwitchStatement):
                switch_children = list(iter_specific_edges(G, node_id, 'AST'))
                case_child = [child_id for child_id in switch_children if isinstance(G.nodes[child_id]['code'], javalang.tree.SwitchStatementCase)]
                expression_child = [child_id for child_id in switch_children if G.nodes[child_id]['label'] == 'expression'][0]
                cfg_edges.append((node_id, expression_child, 'CFG'))
                Parent_children = sorted(list(iter_specific_edges(G, G.nodes[node_id]['parent'], 'AST')))
                if max(Parent_children) > node_id:
                    OutSwitchStmt = Parent_children[Parent_children.index(node_id) + 1]
                judge_node_types((expression_child, G.nodes[expression_child]))
                if len(case_child) == 1:
                    cfg_edges.append((expression_child, case_child[0], 'CFG'))
                    judge_node_types((case_child[0], G.nodes[case_child[0]]))
                    switch_stmts = G.nodes[case_child[0]]['code'].statements
                    switch_stmts_children = list(iter_specific_edges(G, case_child[0], 'AST'))
                    switch_stmts_ID = [child for child in switch_stmts_children if isinstance(G.nodes[child]['code'], javalang.tree.Statement)]
                    if len(switch_stmts_ID) > 0:
                        cfg_edges.append((case_child[0], switch_stmts_ID[0], 'CFG'))
                        judge_node_types((switch_stmts_ID[0], G.nodes[switch_stmts_ID[0]]))
                    if len(switch_stmts_ID) > 1:
                        for i in range(1, len(switch_stmts_ID)):
                            cfg_edges.append((switch_stmts_ID[i - 1], switch_stmts_ID[i], 'CFG'))
                            judge_node_types((switch_stmts_ID[i], G.nodes[switch_stmts_ID[i]]))
                    if isinstance(G.nodes[switch_stmts_ID[len(switch_stmts_ID) - 1]]['code'], 
                                        (javalang.tree.BreakStatement, javalang.tree.ContinueStatement)) == False:
                        if  max(Parent_children) > node_id:
                            cfg_edges.append((switch_stmts_ID[len(switch_stmts_ID) - 1], OutSwitchStmt, 'CFG'))
                    if max(Parent_children) > node_id:
                        cfg_edges.append((case_child[0], OutSwitchStmt, 'CFG'))

                elif len(case_child) > 1:
                    cfg_edges.append((expression_child, case_child[0], 'CFG'))
                    judge_node_types((case_child[0], G.nodes[case_child[0]]))
                    switch_stmts = G.nodes[case_child[0]]['code'].statements
                    switch_stmts_children = list(iter_specific_edges(G, case_child[0], 'AST'))
                    switch_stmts_ID = [child for child in switch_stmts_children if isinstance(G.nodes[child]['code'], javalang.tree.Statement)]
                    if len(switch_stmts_ID) > 0:
                        # switch_first_stmt = [child for child in switch_stmts_children if G.nodes[child]['code'] == switch_stmts_ID[0]][0]
                        cfg_edges.append((case_child[0], switch_stmts_ID[0], 'CFG'))
                        judge_node_types((switch_stmts_ID[0], G.nodes[switch_stmts_ID[0]]))
                    if len(switch_stmts_ID) > 1:
                        for i in range(1, len(switch_stmts_ID)):
                            cfg_edges.append((switch_stmts_ID[i - 1], switch_stmts_ID[i], 'CFG'))
                            judge_node_types((switch_stmts_ID[i], G.nodes[switch_stmts_ID[i]]))
                    for i in range(1, len(case_child)):
                        # switch_stmts_ = G.nodes[case_child[i - 1]]['code'].statements
                        switch_stmts_children_ = list(iter_specific_edges(G, case_child[i - 1], 'AST'))
                        switch_stmts_ID_ = [child for child in switch_stmts_children_ if 'Statement' in str(type(G.nodes[child]['code']))]
                        # switch_final_stmt = [child for child in switch_stmts_children_ if G.nodes[child]['code'] == switch_stmts_[len(switch_stmts_) - 1]][0]
                        if isinstance(G.nodes[switch_stmts_ID_[len(switch_stmts_ID_) - 1]]['code'], 
                                        (javalang.tree.BreakStatement, javalang.tree.ContinueStatement)) == False:
                            cfg_edges.append((switch_stmts_ID_[len(switch_stmts_ID_) - 1], case_child[i], 'CFG'))
                        judge_node_types((case_child[i], G.nodes[case_child[i]]))
                        cfg_edges.append((case_child[i - 1], case_child[i], 'CFG'))
                        judge_node_types((case_child[i], G.nodes[case_child[i]]))

                        # switch_stmts = G.nodes[case_child[i]]['code'].statements
                        switch_stmts_children = list(iter_specific_edges(G, case_child[i], 'AST'))
                        switch_stmts_ID = [child for child in switch_stmts_children if isinstance(G.nodes[child]['code'], javalang.tree.Statement)]
                        if len(switch_stmts_ID) > 0:
                            # switch_first_stmt = [child for child in switch_stmts_children if G.nodes[child]['code'] == switch_stmts[0]][0]
                            cfg_edges.append((case_child[i], switch_stmts_ID[0], 'CFG'))
                            judge_node_types((switch_stmts_ID[0], G.nodes[switch_stmts_ID[0]]))
                        if len(switch_stmts_ID) > 1:
                            for i in range(1, len(switch_stmts_ID)):
                                cfg_edges.append((switch_stmts_ID[i - 1], switch_stmts_ID[i], 'CFG'))
                                judge_node_types((switch_stmts_ID[i], G.nodes[switch_stmts_ID[i]]))
                    if len(list(iter_specific_edges(G, case_child[len(case_child) - 1], 'AST'))) > 0:
                        switch_stmts_final = max(list(iter_specific_edges(G, case_child[len(case_child) - 1], 'AST')))
                    else:
                        switch_stmts_final = case_child[len(case_child) - 1]
                    if max(Parent_children) > node_id:
                        cfg_edges.append((switch_stmts_final, OutSwitchStmt, 'CFG'))
                        cfg_edges.append((case_child[len(case_child) - 1], OutSwitchStmt, 'CFG'))   
        except:
            return cfg_edges
        return cfg_edges

    def get_Break_cfg_edges(current_node: javalang.ast.Node) -> List[Tuple[int, int, str]]:
        node_id = current_node[0]
        node_attr = current_node[1]
        try:
            if isinstance(node_attr['code'], javalang.tree.BreakStatement):
                break_parent = G.nodes[node_id]['parent']
                break_parent_brothers = sorted(list(iter_specific_edges(G, G.nodes[G.nodes[node_id]['parent']]['parent'], 'AST')))
                break_PP = G.nodes[G.nodes[node_id]['parent']]['parent']
                break_PP_brothers = sorted(list(iter_specific_edges(G, G.nodes[G.nodes[G.nodes[node_id]['parent']]['parent']]['parent'], 'AST')))
                if isinstance(G.nodes[break_parent]['code'], (javalang.tree.ForStatement, javalang.tree.SwitchStatement)):
                    if max(break_parent_brothers) > break_parent:
                        breakGoToStmt = break_parent_brothers[break_parent_brothers.index(break_parent) + 1]
                        cfg_edges.append((node_id, breakGoToStmt, 'CFG'))
                        judge_node_types((breakGoToStmt, G.nodes[breakGoToStmt]))
                elif isinstance(G.nodes[break_PP]['code'], (javalang.tree.ForStatement, javalang.tree.SwitchStatement)):
                    if max(break_PP_brothers) > break_PP:
                        breakGoToStmt = break_PP_brothers[break_PP_brothers.index(break_PP) + 1]
                        cfg_edges.append((node_id, breakGoToStmt, 'CFG'))
                        judge_node_types((breakGoToStmt, G.nodes[breakGoToStmt]))
        except:
            return cfg_edges
        return cfg_edges

    def get_Continue_cfg_edges(current_node: javalang.ast.Node) -> List[Tuple[int, int, str]]:
        node_id = current_node[0]
        node_attr = current_node[1]
        try:
            if isinstance(node_attr['code'], javalang.tree.ContinueStatement):
                continue_parent = G.nodes[node_id]['parent']
                continue_PP = G.nodes[G.nodes[node_id]['parent']]['parent']
                continue_PPP = G.nodes[G.nodes[G.nodes[node_id]['parent']]['parent']]['parent']
                if isinstance(G.nodes[continue_parent]['code'], javalang.tree.ForStatement):
                    cfg_edges.append((node_id, continue_parent, 'CFG'))
                    judge_node_types((continue_parent, G.nodes[continue_parent]))
                elif isinstance(G.nodes[continue_PP]['code'], javalang.tree.ForStatement):
                    cfg_edges.append((node_id, continue_PP, 'CFG'))
                    judge_node_types((continue_PP, G.nodes[continue_PPP]))
                elif isinstance(G.nodes[continue_PPP]['code'], javalang.tree.ForStatement):
                    cfg_edges.append((node_id, continue_PPP, 'CFG'))
                    judge_node_types((continue_PPP, G.nodes[continue_PPP]))
        except:
            return cfg_edges
        return cfg_edges

    def get_synchronized_cfg_edges(current_node: javalang.ast.Node) -> List[Tuple[int, int, str]]:
        node_id = current_node[0]
        node_attr = current_node[1]
        synchronizedParent_children = sorted(list(iter_specific_edges(G, G.nodes[node_id]['parent'], 'AST')))
        try:
            if isinstance(node_attr['code'], javalang.tree.SynchronizedStatement):
                synchronized_children = list(iter_specific_edges(G, node_id, 'AST'))
                lock_children = [child for child in synchronized_children if G.nodes[child]['label'] == 'lock']
                block_children = [child for child in synchronized_children if G.nodes[child]['label'] == 'block']
                cfg_edges.append((node_id, lock_children[0], 'CFG'))
                if max(synchronizedParent_children) > node_id:
                    OutSwitchStmt = synchronizedParent_children[synchronizedParent_children.index(node_id) + 1]
                else:
                    OutSwitchStmt = node_id
                judge_node_types((lock_children[0], G.nodes[lock_children[0]]))
                if len(lock_children) > 1:
                    for i in range(1, len(lock_children)):
                        cfg_edges.append((lock_children[i -1], lock_children[i], 'CFG'))
                        judge_node_types((lock_children[i], G.nodes[lock_children[i]]))
                if len(block_children) > 0:
                    cfg_edges.append((lock_children[len(lock_children) - 1], block_children[0], 'CFG'))
                    judge_node_types((block_children[0], G.nodes[block_children[0]]))
                    if len(block_children) > 1:
                        for i in range(1, len(lock_children)):
                            cfg_edges.append((block_children[i -1], block_children[i], 'CFG'))
                            judge_node_types((block_children[i], G.nodes[block_children[i]]))
                    cfg_edges.append((block_children[len(block_children) - 1], OutSwitchStmt, 'CFG'))
        except:
            return cfg_edges

    def get_try_catch_finally_block(current_node: javalang.ast.Node) -> List[Tuple[int, int, str]]:
        node_id = current_node[0]
        node_attr = current_node[1]
        try:
            if isinstance(node_attr['code'], javalang.tree.TryStatement):
                try_catch_finally_children = list(iter_specific_edges(G, node_id, 'AST'))
                try_resources = [child for child in try_catch_finally_children if G.nodes[child]['label'] == 'resources']
                blocks = [child for child in try_catch_finally_children if G.nodes[child]['label'] == 'block']
                catches_ = [child for child in try_catch_finally_children if G.nodes[child]['label'] == 'catches']
                finally_blocks = [child for child in try_catch_finally_children if G.nodes[child]['label'] == 'finally_block']
                    # block -> cfg edges
                if len(blocks) > 0:
                    if len(try_resources) == 0:
                        cfg_edges.append((node_id, blocks[0], 'CFG'))
                        judge_node_types((blocks[0], G.nodes[blocks[0]]))
                    else:
                        cfg_edges.append((node_id, try_resources[0], 'CFG'))
                        judge_node_types((try_resources[0], G.nodes[try_resources[0]]))
                        if len(try_resources) > 1:
                            for i in range(len(try_resources)):
                                cfg_edges.append((try_resources[i - 1], try_resources[i], 'CFG'))
                                judge_node_types((try_resources[i], G.nodes[try_resources[i]]))
                        cfg_edges.append((try_resources[len(try_resources) - 1], blocks[0], 'CFG'))
                        judge_node_types((blocks[0], G.nodes[blocks[0]]))
                        
                    if len(blocks) > 1:
                        for i in range(1, len(blocks)):
                            cfg_edges.append((blocks[i - 1], blocks[i], 'CFG'))
                            judge_node_types((blocks[i], G.nodes[blocks[i]]))

                # catches -> cfg edges 
                if len(catches_) > 0:
                    catches = catches_[0]
                    cfg_edges.append((blocks[len(blocks) - 1], catches, 'CFG'))
                    catches_children = list(iter_specific_edges(G, catches, 'AST'))
                    catch_blocks = [child for child in catches_children if G.nodes[child]['label'] == 'block']
                    catch_parameter = [child for child in catches_children if G.nodes[child]['label'] == 'parameter'][0]
                    cfg_edges.append((catches, catch_parameter, 'CFG'))
                    if len(catch_blocks) > 0:
                        cfg_edges.append((catch_parameter, catch_blocks[0], 'CFG'))
                        judge_node_types((catch_blocks[0], G.nodes[catch_blocks[0]]))
                        if len(catch_blocks) > 1:
                            for i in range(1, len(catch_blocks)):
                                cfg_edges.append((catch_blocks[i - 1], catch_blocks[i], 'CFG'))
                                judge_node_types((catch_blocks[i], G.nodes[catch_blocks[i]]))
                            if len(finally_blocks) > 0:
                                cfg_edges.append((catch_blocks[len(catch_blocks) - 1], finally_blocks[0], 'CFG'))
                                judge_node_types((finally_blocks[0], G.nodes[finally_blocks[0]]))
                # finally_blocks -> cfg edges
                if len(finally_blocks) > 0 and isinstance(catches_, int):
                    cfg_edges.append((catch_parameter, finally_blocks[0], 'CFG'))
                    judge_node_types((finally_blocks[0], G.nodes[finally_blocks[0]]))
                elif len(finally_blocks) > 0 and len(catches_) == 0:
                    cfg_edges.append((blocks[len(blocks) - 1], finally_blocks[0], 'CFG'))
                    judge_node_types((finally_blocks[0], G.nodes[finally_blocks[0]]))
                    if len(finally_blocks) > 1:
                        for i in range(1, len(finally_blocks)):
                            cfg_edges.append((finally_blocks[i - 1], finally_blocks[i], 'CFG'))
                            judge_node_types((finally_blocks[i], G.nodes[finally_blocks[i]]))
                # outStmt
                if len(finally_blocks) > 0:
                    cfg_edges.append((finally_blocks[len(finally_blocks) -1], node_id, 'CFG'))
                elif len(catches_) > 0:
                    catch_blocks = [child for child in catches_children if G.nodes[child]['label'] == 'block']
                    catch_parameter = [child for child in catches_children if G.nodes[child]['label'] == 'parameter'][0]
                    if len(catch_blocks) > 0:
                # elif len(catch_blocks) > 0:
                        cfg_edges.append((catch_blocks[len(catch_blocks) -1], node_id, 'CFG'))
                        cfg_edges.append((catch_parameter, node_id, 'CFG'))
                    elif len(blocks) > 0:
                        cfg_edges.append((blocks[len(blocks) -1], node_id, 'CFG'))
                        cfg_edges.append((catch_parameter, node_id, 'CFG'))
        except:
            return cfg_edges
        return cfg_edges

    def get_cfg_edges_for_a_method(G: nx.MultiDiGraph) -> List[Tuple[int, int, str]]:
        '''This function is to generate all CFG edges of a method.'''
        current_node = G.nodes[0]
        try:
            if isinstance(current_node['code'], javalang.tree.MethodDeclaration):
                func_children = list(iter_specific_edges(G, 0, 'AST'))
                func_body_stmts = [child for child in func_children if G.nodes[child]['label'] == 'body']
                if len(func_body_stmts) > 0:
                    cfg_edges.append((0, func_body_stmts[0], 'CFG'))
                    judge_node_types((func_body_stmts[0], G.nodes[func_body_stmts[0]]))
                    if len(func_body_stmts) > 1:
                        for i in range(1, len(func_body_stmts)):
                            if not isinstance(G.nodes[func_body_stmts[i - 1]]['code'], CFGType):
                                cfg_edges.append((func_body_stmts[i - 1], func_body_stmts[i], 'CFG'))
                            judge_node_types((func_body_stmts[i], G.nodes[func_body_stmts[i]])) 
        except:
            return cfg_edges
        return cfg_edges
    
    cfg_edges = get_cfg_edges_for_a_method(G)
    return list(set(cfg_edges))

def get_cfg_nodes(G: nx.MultiDiGraph) -> List[int]:
    cfg_nodes = []
    for edge in G.edges.data():
        if edge[2]['label'] == 'CFG':
            cfg_nodes.append(edge[0])
            cfg_nodes.append(edge[1])
    return list(set(cfg_nodes))

def add_cfg_to_ast(G: nx.MultiDiGraph, cfg_edges: List[Tuple[int, int, str]]) -> nx.MultiDiGraph:
    for i in range(len(cfg_edges)):
        G.add_edge(cfg_edges[i][0], cfg_edges[i][1], label = cfg_edges[i][2])
    return G

# ----------------------------------------------------------------
# add DFG to ASTGraph
# ----------------------------------------------------------------

def get_Def_Use_edges(G: nx.MultiDiGraph) -> List[Tuple[str, List[int], List[int]]]:
    '''
    This function is used to generate DFG edges.
    Return: List[Tuple[str, int, list[int]]] -> (variable name, variable_def_node_id, list[variable_use_node_ids])
    '''
    def get_def_vars() -> List[Tuple[str, int, List[int]]]:
        '''
        This function is used to get the names (str) and node IDs (int) of variables in a method.
        '''
        for node in G.nodes.data():
            def_nodes = []
            node_id = node[0]

            if isinstance(node[1]['code'], javalang.tree.MethodDeclaration):
                    def_var_children = list(iter_specific_edges(G, node_id, 'AST'))
                    def_parameters = [child for child in def_var_children if G.nodes[child]['label'] == 'parameters']
                    for para in def_parameters:
                        if isinstance(G.nodes[para]['code'], javalang.tree.FormalParameter):
                            var_name = G.nodes[para]['code'].name
                            if len(dfg_DefUse) > 0 and var_name in [DefUse[0] for DefUse in dfg_DefUse]:
                                index = [DefUse[0] for DefUse in dfg_DefUse].index(var_name)
                                dfg_DefUse[index][1].append(node_id)
                            else:
                                def_nodes.append(node_id)
                                dfg_DefUse.append((var_name, def_nodes, []))
            if isinstance(node[1]['code'], (DFGDefType_declators, DFGDefType_name_value, javalang.tree.StatementExpression)):
                if isinstance(node[1]['code'], DFGDefType_declators):
                    def_var_children = list(iter_specific_edges(G, node_id, 'AST'))
                    def_declarators = [child for child in def_var_children if G.nodes[child]['label'] == 'declarators']
                    for declarator in def_declarators:
                        if isinstance(G.nodes[declarator]['code'], DFGType_name):
                            # if G.nodes[declarator]['code'].name not in [DefUse[0] for DefUse in dfg_DefUse]:
                            if len(dfg_DefUse) > 0 and G.nodes[declarator]['code'].name in [DefUse[0] for DefUse in dfg_DefUse]:
                                index = [DefUse[0] for DefUse in dfg_DefUse].index(G.nodes[declarator]['code'].name)
                                dfg_DefUse[index][1].append(node_id)
                            else:
                                def_nodes.append(node_id)
                                dfg_DefUse.append((G.nodes[declarator]['code'].name, def_nodes, []))
                        elif isinstance(G.nodes[declarator]['code'], DFGType_member):
                            # if G.nodes[declarator]['code'].member not in [DefUse[0] for DefUse in dfg_DefUse]:
                            if len(dfg_DefUse) > 0 and G.nodes[declarator]['code'].member in [DefUse[0] for DefUse in dfg_DefUse]:
                                index = [DefUse[0] for DefUse in dfg_DefUse].index(G.nodes[declarator]['code'].member)
                                dfg_DefUse[index][1].append(node_id)
                            else:
                                def_nodes.append(node_id)
                                dfg_DefUse.append((G.nodes[declarator]['code'].name, def_nodes, []))
                elif isinstance(node[1]['code'], DFGDefType_name_value):
                    def_var_children = list(iter_specific_edges(G, node_id, 'AST'))
                    def_creators = [child for child in def_var_children if G.nodes[child]['label'] == 'value']
                    for creator in def_creators:
                        if isinstance(G.nodes[creator]['code'], DFGUseType_arguments):
                            if len(dfg_DefUse) > 0 and G.nodes[node_id]['code'].name in [DefUse[0] for DefUse in dfg_DefUse]:
                                index = [DefUse[0] for DefUse in dfg_DefUse].index(G.nodes[node_id]['code'].name)
                                dfg_DefUse[index][1].append(node_id)
                            else:
                                def_nodes.append(node_id)
                                dfg_DefUse.append((G.nodes[node_id]['code'].name, def_nodes, []))
                elif isinstance(node[1]['code'], javalang.tree.StatementExpression):
                    if isinstance(node[1]['code'].expression, javalang.tree.Assignment) and node[1]['code'].expression.type == '=':
                        def_var_children = list(iter_specific_edges(G, node_id, 'AST'))
                        var_name = ''
                        expression = [child for child in def_var_children if G.nodes[child]['label'] == 'expression'][0]
                        if isinstance(G.nodes[expression]['code'].expressionl, javalang.tree.MemberReference):
                            if G.nodes[expression]['code'].expressionl.qualifier not in ['', None]:
                                var_name = G.nodes[expression]['code'].expressionl.qualifier + '.' + G.nodes[expression]['code'].expressionl.member
                            else:
                                var_name = G.nodes[expression]['code'].expressionl.member
                            if len(dfg_DefUse) > 0 and var_name in [DefUse[0] for DefUse in dfg_DefUse]:
                                index = [DefUse[0] for DefUse in dfg_DefUse].index(var_name)
                                dfg_DefUse[index][1].append(node_id)
                            else:
                                def_nodes.append(node_id)
                                dfg_DefUse.append((var_name, def_nodes, []))
                        if isinstance(G.nodes[expression]['code'].expressionl, javalang.tree.This):
                            var_name = 'this.'
                            if len(G.nodes[expression]['code'].expressionl.selectors) > 0:
                                for selector in G.nodes[expression]['code'].expressionl.selectors:
                                    if isinstance(selector, javalang.tree.MemberReference):
                                        if selector.qualifier in ['', None]:
                                            var_name += selector.member
                                        else:
                                            var_name += selector.qualifier + '.' + selector.member
                            if len(dfg_DefUse) > 0 and var_name in [DefUse[0] for DefUse in dfg_DefUse]:
                                index = [DefUse[0] for DefUse in dfg_DefUse].index(var_name)
                                dfg_DefUse[index][1].append(node_id)
                            else:
                                def_nodes.append(node_id)
                                dfg_DefUse.append((var_name, def_nodes, []))
        return dfg_DefUse
    
    def get_use_vars() -> List[Tuple[str, List[int], List[int]]]:
        '''
        This function is used to get the node ids where the variables in a method are used.
        parameter: 1) use_node_type: 
        '''
        var_names = [defuse[0] for defuse in dfg_DefUse]
        use_var_nodes = [defuse[2] for defuse in dfg_DefUse]
        var_def_node = [defuse[1] for defuse in dfg_DefUse]

        for node in G.nodes.data():
            node_id = node[0]
            node_attrs = node[1]
            
            if isinstance(node_attrs['code'], javalang.tree.MemberReference):
                parent_node = G.nodes[node_id]['parent']
                if not isinstance(G.nodes[parent_node]['code'], javalang.tree.This):
                    if node_attrs['code'].qualifier in ['', None]:
                        var_name = node_attrs['code'].member
                    else:
                        var_name = node_attrs['code'].member + '.' + node_attrs['code'].qualifier
                    if var_name not in var_names:
                    #     index = var_names.index(var_name)
                    #     use_var_node = get_use_var_node(G, node_id)
                    #     if use_var_node not in use_var_nodes[index]:
                    #         use_var_nodes[index].append(use_var_node)
                    # else:  
                        # var_names.append(var_name)
                        dfg_DefUse.append((var_name, [-1], [parent_node]))          

                else:
                    if G.nodes[node_id]['label'] == 'selectors':
                        if node_attrs['code'].qualifier in ['', None]:
                            var_name = 'this.' + node_attrs['code'].member
                        else:
                            var_name = 'this.' + node_attrs['code'].member + '.' + node_attrs['code'].qualifier
                        if var_name not in var_names:
                        #     index = var_names.index(var_name)
                        #     use_var_node = get_use_var_node(G, node_id)
                        #     if use_var_node not in use_var_nodes[index]:
                        #         use_var_nodes[index].append(use_var_node)
                        # else:
                            dfg_DefUse.append((var_name, [-1], [G.nodes[parent_node]['parent']]))
        
        var_names = [defuse[0] for defuse in dfg_DefUse]
        use_var_nodes = [defuse[2] for defuse in dfg_DefUse]
        var_def_node = [defuse[1] for defuse in dfg_DefUse]
        for node in G.nodes.data():
            node_id = node[0]
            node_attrs = node[1]   
            # else:
            for i in range(len(var_names)):
                # if '=' + str(var_names[i]) +',' in str(G.nodes[node_id]['code']):
                if len(re.findall(r'=' + str(var_names[i]) + r'(\+|\-|\*|\\)\d+,', str(G.nodes[node_id]['code']), flags=re.S)) > 0 or ('=' + str(var_names[i]) +',' in str(G.nodes[node_id]['code'])):
                    # use_var_node = get_use_var_node(G, node_id)
                    use_var_node = node_id
                    if use_var_node not in use_var_nodes[i] and use_var_node not in var_def_node[i] and use_var_node != 0 and  (isinstance(node[1]['code'], 
                                (javalang.tree.Statement, javalang.tree.CatchClauseParameter, javalang.tree.CatchClause, javalang.tree.TryResource, javalang.tree.Invocation,
                                javalang.tree.BinaryOperation, javalang.tree.Declaration, javalang.tree.ForControl, javalang.tree.EnhancedForControl)) or  node[1]['label'] == 'condition'):
                        use_var_nodes[i].append(use_var_node)
                        use_var_nodes[i] = filter_var_use_nodes(G, use_var_nodes[i], node_id)
        return dfg_DefUse


    dfg_DefUse = []
    dfg_DefUse = get_def_vars()
    dfg_DefUse = get_use_vars()
    return dfg_DefUse

def filter_var_use_nodes(G: nx.MultiDiGraph, use_var_node: List[int], node_id):
    parent = G.nodes[node_id]['parent']
    if parent in use_var_node:
        use_var_node.remove(parent)
    return use_var_node


def get_use_var_node(G: nx.MultiDiGraph, node_id: int) -> int:
    parent_nodes = []
    cfg_nodes = get_cfg_nodes(G)
    parent_nodes = Recursion_get_parents(G, node_id, parent_nodes)
    parent_ = -2
    for parent in parent_nodes:
        if parent in cfg_nodes:
            parent_ = parent
            break
    return parent_

def get_dfg_edges(dfg_DefUse: List[Tuple[str, List[int], List[int]]]) -> List[Tuple[int, int, str]]:
    dfg_edges = []
    var_names = [DefUse[0] for DefUse in dfg_DefUse]
    var_def_nodes = [sorted(list(set(DefUse[1]))) for DefUse in dfg_DefUse]
    var_use_nodes = [sorted(list(set(DefUse[2]))) for DefUse in dfg_DefUse]

    for i in range(len(var_names)): # var
        def_use_indexs = []
        if len(var_def_nodes[i]) > 0 and len(var_use_nodes[i]) > 0:
            for j in range(len(var_def_nodes[i])):
                for k in range(len(var_use_nodes[i])):
                    if var_def_nodes[i][j] < var_use_nodes[i][k]:
                        def_use_indexs.append(k)
                        break
            if len(def_use_indexs) > 0:
                for j in range(len(def_use_indexs)):
                    dfg_edges.append((var_def_nodes[i][j], var_use_nodes[i][def_use_indexs[j]], 'DFG_DefUse'))
                if len(def_use_indexs) == 1:
                    for j in range(def_use_indexs[0], len(var_use_nodes[i]) - 1):
                        dfg_edges.append((var_use_nodes[i][j], var_use_nodes[i][j + 1], 'DFG_UseUse'))
                else:
                    for j in range(1, len(def_use_indexs)):
                        for k in range(def_use_indexs[j - 1], def_use_indexs[j] - 1):
                            dfg_edges.append((var_use_nodes[i][k], var_use_nodes[i][k + 1], 'DFG_UseUse'))
                    for j in range(def_use_indexs[len(def_use_indexs) - 1], len(var_use_nodes[i]) - 1):
                        dfg_edges.append((var_use_nodes[i][j], var_use_nodes[i][j + 1], 'DFG_UseUse'))
    return dfg_edges

def add_dfg_to_ast(G: nx.MultiDiGraph, dfg_edges: List[Tuple[int, int, str]]) -> nx.MultiDiGraph:
    for i in range(len(dfg_edges)):
        G.add_edge(dfg_edges[i][0], dfg_edges[i][1], label = dfg_edges[i][2])
    return G

# ----------------------------------------------------------------
# utils for nx.MultiGraph, doesn't necessarily concerned with code
# ----------------------------------------------------------------
def Recursion_get_parents(G: nx.MultiDiGraph, node_id: int, parent_nodes: List[int]) -> List[int]:
    parent_nodes.append(node_id)
    node_parent = G.nodes[node_id]['parent']
    if node_parent != -1 and not isinstance(G.nodes[node_parent], (javalang.tree.Statement, javalang.tree.Declaration, javalang.tree.MethodDeclaration)):
        Recursion_get_parents(G, node_parent, parent_nodes)
    return parent_nodes 

def iter_specific_edges(G: nx.MultiDiGraph, u: int, edge_type: str) -> Iterable[int]:
    """In our graph, there may exist many type of edges between two nodes.
    Sometimes, we may just want to walk along a specific type of edge
    """
    for successor in G.successors(u):
        if exist_edge(G, u, successor, edge_type):
            yield successor

def exist_edge(G: nx.MultiDiGraph, u: int, v: int, edge_type: str) -> bool:
    """Judge if there is a specific type of edge in (u, v)"""
    for d in G[u][v].values():
        if d['label'] == edge_type:
            return True
    return False


def find_leftest_most(G: nx.MultiDiGraph, node_id: int, edge_type: str = 'AST') -> int:
    """ Find the most left node of a specific node_id along with a specific edge type"""
    while children := list(iter_specific_edges(G, node_id, edge_type)):
        if len(children) == 0:
            return node_id
        else:
            node_id = children[0]
    return node_id


def find_rightest_most(G: nx.MultiDiGraph, node_id: int, edge_type: str = 'AST') -> int:
    """ Find the most right node of a specific node_id along with a specific edge type"""
    while children := list(iter_specific_edges(G, node_id, edge_type)):
        if len(children) == 0:
            return node_id
        else:
            node_id = children[-1]
    return node_id


def main():
    dataFilePath = r'./data.pkl'
    data = read_data(dataFilePath)
    funcAST = data['func_ast'][0][0][3]
    G, terminals = construct_ast_graph(funcAST, treeNodeType)
    for node in G.nodes.data():
        print(node)
    print('*' * 20)
    cfg_edges = get_cfg_edges(G)
    print(cfg_edges)
    print('*' * 20)
    G = add_cfg_to_ast(G, cfg_edges)
    for edge in G.edges.data():
        if edge[2]['label'] == 'CFG':
            print(edge)
    print('*' * 20)
    dfg_DefUse = get_Def_Use_edges(G)
    print(dfg_DefUse)
    print('*' * 50)
    defg_edges = get_dfg_edges(dfg_DefUse)
    print(defg_edges)
    print('*' * 50)
    G = add_dfg_to_ast(G, defg_edges)
    for edge in G.edges.data():
        if edge[2]['label'] == 'DFG_DefUse':
            print(edge)

    for edge in G.edges.data():
        if edge[2]['label'] == 'DFG_UseUse':
            print(edge)

if __name__ == '__main__':
    main()
