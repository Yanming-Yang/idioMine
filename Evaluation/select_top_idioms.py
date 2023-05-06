import pandas as pd
import typing
import argparse
import difflib

def top_idioms(args):
    top_idioms = []
    idiom_completions = pd.read_pickle(args.idioms)
    clusters = pd.read_pickle(args.clusters)

    idioms = idiom_completions['pattern_completion']
    judges = idiom_completions['final_completion']

    sub_idioms = clusters['center_point']
    cluster_size = clusters['cluster_size']


    for i in range(len(judges)):
        judge = judges[i]['choices'][0]['message']['content']
        if 'Yes' in judge.replace('\n', '') or 'yes' in judge.replace('\n', ''):
            if  isinstance(idioms[i], str):
                idiom = idioms[i]
            else:
                idiom = str(idioms[i]['choices'][0]['message']['content'])
            if  'super.' not in idiom and idiom != '' and idiom != ' ':
                for j in range(len(sub_idioms)):
                    # if str(sub_idioms[i]) in idiom:
                    if difflib.SequenceMatcher(None, str(sub_idioms[i]), idiom).quick_ratio() > 0.2:
                        top_idioms.append([idiom, cluster_size[j]])
                        break

    df_top_idioms = pd.DataFrame(top_idioms, columns=['Idiom', 'Cluster_Size'])
    df_top_idioms.sort_values(by='Cluster_Size', ascending=True)
    pd.to_pickle(df_top_idioms, args.output)
    return df_top_idioms


def get_useful_idioms(args):
    idiom_completions = pd.read_pickle(args.idioms)
    idioms = idiom_completions['pattern_completion']
    judges = idiom_completions['judge_completion']

    idiom_list = []
    final_list = []
    dataset_list = []

    for i in range(len(judges)):
        judge = judges[i]['choices'][0]['message']['content']
        if 'Yes' in judge.replace('\n', '') or 'yes' in judge.replace('\n', ''):
            if  isinstance(idioms[i], str):
                idiom = idioms[i]
            else:
                idiom = str(idioms[i]['choices'][0]['message']['content'])
            if 'return' not in idiom and 'super.' not in idiom and 'this.' not in idiom and idiom != '' and idiom != ' ' and 'sorry' not in idiom and 'identical' not in idiom:
                if ';' in idiom or '{' in idiom:
                    dataset_list.append(args.idioms)
                    final_list.append(judge)
                    idiom_list.append(idiom)


    data = pd.DataFrame({'pro/lib': dataset_list, 'idiom': idiom_list, 'final': final_list})
    data.to_csv( args.output)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='args description')
    parser.add_argument('--idioms', '-iDF', type=str, help='the input file')
    parser.add_argument('--output', '-OT', type=str, help='the input file')
    args = parser.parse_args()
    get_useful_idioms(args)

