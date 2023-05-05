import pandas as pd 
import javalang
import os
from javalang import ast
from typing import List
import argparse

class GetJavaFile:
    '''
    this class is to extract all Java files in 919 real-world projects.
    '''
    def __init__(self, projects: List[str], pro_file_list: List[str]) -> None:
        self.projects = projects
        self.pro_file_list = pro_file_list

    def get_Java_projects(self, PathStr: str):
        for root, dirs, files in os.walk(PathStr):
            self.projects = dirs
            break

    def get_all_java_files(self, PathStr: str):
        for projectStr in self.projects:
            files_list = []
            for root, dirs, files in os.walk(PathStr + '/' + projectStr):
                if len(files) > 0:
                    for file_ in files:
                        if '.java' in file_ and 'Test' not in file_ and 'test' not in file_ and 'Test' not in root and 'test' not in root:
                            files_list.append(root + '/' + file_)
            self.pro_file_list.append(files_list)
        # return files_list 

class getASTFunctions:
    '''
    this class is to transform Java functions into AST
    '''
    def __init__(self, JavaFile: str, funcASTs: List) -> None:
        self.JavaFile = JavaFile
        self.funcASTs = funcASTs

    def trans_file_to_AST(self):
        try:
            programfile = open(self.JavaFile, encoding='latin-1')
            programtext = programfile.read()
            tree = javalang.parse.parse(programtext)
        except (javalang.tokenizer.LexerError, Exception):
            tree = None
        return tree

    def get_func_ASTs(self, fileTree):
        # class_ = fileTree.children[2][0]
        # self.funcASTs = [unit for unit in class_.body if 'MethodDeclaration' in str(type(unit))]
        # self.funcASTs = [node for path, node in fileTree.filter(javalang.tree.MethodDeclaration)]
        if fileTree != None:
            try:
                self.funcASTs = [node for path, node in fileTree.filter(javalang.tree.MethodDeclaration)]
            except:
                self.funcASTs = None
        else:
            self.funcASTs = None

def filter_no_func_file(GJF: GetJavaFile, pro_func_ast: List[javalang.ast.Node]):
    pro_files_ = []
    pro_funcs_ = []
    pro_files = []
    pro_funcs = []
    for i in range(len(GJF.projects)):
        for j in range(len(pro_func_ast[i])):
            if pro_func_ast[i][j] != None and len(pro_func_ast[i][j]) != 0:
                pro_files_.append(GJF.pro_file_list[i][j])
                pro_funcs_.append(pro_func_ast[i][j])
        pro_files.append(pro_files_)
        pro_funcs.append(pro_funcs_)
    return pro_files, pro_funcs

def write_data(GJF: GetJavaFile, pro_func_ast: List[javalang.ast.Node], dataFilePath: str):
    pro_files, pro_funcs = filter_no_func_file(GJF, pro_func_ast)
    data = pd.DataFrame({'project':GJF.projects, 'javaFile': pro_files, 'func_ast':pro_funcs})
    pd.to_pickle(data, dataFilePath)

def read_data(dataFilePath: str):
    data = pd.read_pickle(dataFilePath)
    return data

def main():
    projects = []
    data_files = []
    pro_func_ast = []

    parser = argparse.ArgumentParser(description='args description')
    parser.add_argument('--PathStr', '-PS', help='the path of the input project')
    parser.add_argument('--dataFilePath', '-dFP', help='the output file')

    # PathStr = r'./repos_new/repos_9'

    args = parser.parse_args()
    GJF = GetJavaFile(projects, data_files)
    GJF.get_Java_projects(args.PathStr)
    for i in range(len(GJF.projects)):
        print(GJF.projects[i])
        funcs_in_pro = []
        GJF.get_all_java_files(args.PathStr)
        for pro_file_tmp in GJF.pro_file_list[i]:
            # take pro_file_list[0][1] as an example and generate functions' ASTs in this file
            funcASTs = []
            Parser = getASTFunctions(pro_file_tmp, funcASTs)
            tree = Parser.trans_file_to_AST()
            Parser.get_func_ASTs(tree)
            funcs_in_pro.append(Parser.funcASTs)
        pro_func_ast.append(funcs_in_pro)

    # dataFilePath = r'./library_data_new_9.pkl'
    
    write_data(GJF, pro_func_ast, args.dataFilePath)

if __name__ == "__main__":
    main()
   


