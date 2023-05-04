import pandas as pd
import argparse

def read_effective_data_in_a_pro(dataFile):
    data = pd.read_pickle(dataFile)
    idioms = data['pattern_completion']
    final_idioms = data['final_completion']
    judge_idioms = data['judge_completion']
    explaination = data['situation_completion']

    real_idioms = []
    finals = []
    judge_idioms_list = []
    explaination_idiom = []
    
    for i in range(len(final_idioms)):
        judge_content_i = final_idioms[i]['choices'][0]['message']['content']
        if 'Yes' in judge_content_i.replace('\n', '') or 'yes' in judge_content_i.replace('\n', ''):
            finals.append(judge_content_i)
            if judge_idioms[i] != None:
                judge_idioms_list.append(judge_idioms[i]['choices'][0]['message']['content'])
            else:
                judge_idioms_list.append('0')
            if explaination[i] != None:
                explaination_idiom.append(explaination[i]['choices'][0]['message']['content'])
            else:
                explaination_idiom.append('0')
            if isinstance(idioms[i], str):
                real_idioms.append(idioms[i])
            else:
                real_idioms.append(idioms[i]['choices'][0]['message']['content'])
    
    return real_idioms, judge_idioms_list, explaination_idiom, finals

if __name__ == '__main__':   
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataFile', type=str, help='The file path of effective data')
    args = parser.parse_args()

    real_idioms, judges, explaination_idiom, finals = read_effective_data_in_a_pro(args.dataFile)

    idx = 0
    real_idioms_list = []
    for i in range(len(real_idioms)):
        if not (real_idioms[i].count(';') == 1 and ('this' in real_idioms[i] or 'return' in real_idioms[i] or 'super' in real_idioms[i])):
            # if '{' in real_idioms[i] or '?' in real_idioms[i] or real_idioms[i].count(';') > 1:
            if '{' in real_idioms[i] or '?' in real_idioms[i] or  real_idioms[i].count('=') > 0:
                if not (real_idioms[i].count('=') > 0 and real_idioms[i].split('=')[0].strip().count(' ') == 0):
                    print(idx, real_idioms[i])
                    # print(idx, real_idioms[i] + '\n', judges[i] + '\n')
                    # print(libraries_idiom[i] + '\n', explaination_idiom[i] + '\n')
                    print('*' * 50)
                    idx += 1
    print(idx)

    





