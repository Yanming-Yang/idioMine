import openai
import pandas as pd
from difflib import SequenceMatcher
from prompts import prompts
import traceback
import argparse 
import time

def get_pattern_result(cluster_data_file, prompts, completion_result_file, completion_result_file_single, k):
    cluster_data = pd.read_pickle(cluster_data_file)
    cluster_center_points_all = cluster_data['center_point']
    cluster_labels = cluster_data['label']
    cluster_center_point_infos = cluster_data['center_point_info']
    # cluster_sizes = cluster_data['cluster_size']

    completion_result = pd.DataFrame(columns=['pattern_completion', 'judge_completion', 'situation_completion', 'final_completion'])

    cluster_center_points = cluster_center_points_all
    combine_result = []
    combine_result.append(cluster_center_points)
    combine_result_info = []
    combine_result_info.append(cluster_center_point_infos)
    index_result = [[-1] for i in range(len(cluster_center_points_all))]

    def single_pattern_result(combine_result_info_j, combine_result):
        try:
            for i in range(len(combine_result_info_j)):
                if type(combine_result_info_j[i]) == tuple:
                    completion = combine_result[i]
                    print(completion)
                    judge_completion = whether_a_code_pattern(completion)
                    libraries_completion = used_pattern_libraries(completion)
                    situation_completion = situation_suggestion(completion)
                    final_completion = final_qustion(completion)
                    if 'no' not in final_completion['choices'][0]['message']['content'] or 'No' not in final_completion['choices'][0]['message']['content']:
                        completion_result.loc[len(completion_result.index)] = [completion, judge_completion, situation_completion, final_completion]
                print(i)
            pd.to_pickle(completion_result, completion_result_file_single)
        except:
            pd.to_pickle(completion_result, completion_result_file_single)
            traceback.print_exc()


    def iter_pattern_result(combine_result_j, combine_result_info_j, index_result_j, j):
        iter_result_j_ = []
        index_result_j_ = []
        combine_result_info_j_ = []
        completion_result_file_combine = completion_result_file + 'combine{j}.pkl'.format(j=j)
        try:
            for i in range(len(combine_result_info_j)):
                for x in range(len(cluster_center_points_all)):
                    if x not in index_result_j and type(cluster_center_point_infos[x]) == tuple and type(combine_result_info_j[i]) == tuple and cluster_center_point_infos[x][0] == combine_result_info_j[i][0] and cluster_center_point_infos[x][1] == combine_result_info_j[i][1] and cluster_center_point_infos[x][2] == combine_result_info_j[i][2]:
                        m = SequenceMatcher(None, cluster_center_points_all[x], combine_result_j[i])
                        match = m.find_longest_match(0, len(cluster_center_points_all[x]), 0, len(combine_result_j[i]))
                        if match.size > 5 and cluster_center_points_all[x] != combine_result_j[i]:
                            # print(cluster_center_points_all[x])
                            # print(combine_result_j[i])
                            completion = get_synthesized_pattern(cluster_center_points_all[x], combine_result_j[i])
                            code_completion = completion['choices'][0]['message']['content']
                            judge_completion = whether_a_code_pattern(code_completion)
                            # libraries_completion = used_pattern_libraries(code_completion)
                            situation_completion = situation_suggestion(code_completion)
                            final_completion = final_qustion(code_completion)
                            if 'no' not in final_completion['choices'][0]['message']['content'] or 'No' not in final_completion['choices'][0]['message']['content']:
                                iter_result_j_.append(code_completion)
                                index_result_j_.append([i-1, i])
                                combine_result_info_j_.append(cluster_center_point_infos[i])
                            # else:
                            #     libraries_completion = None
                            #     situation_completion = None
                            completion_result.loc[len(completion_result.index)] = [completion, judge_completion, situation_completion, final_completion]
                #     print('x', x)
                # print('i', i)
                # print('j', j)
            pd.to_pickle(completion_result, completion_result_file_combine)
        except:
            pd.to_pickle(completion_result, completion_result_file_combine)
            traceback.print_exc()
        return iter_result_j_, combine_result_info_j_, index_result_j_
    
    learned_prompt(prompts)
    single_pattern_result(cluster_center_point_infos, cluster_center_points_all)

    for j in range(k): 
        combine_result_j, combine_result_info_j, index_result_j = iter_pattern_result(combine_result[j], combine_result_info[j], index_result[j], j)
        combine_result.append(combine_result_j)
        combine_result_info.append(combine_result_info_j)
        index_result.append(index_result_j)

def learned_prompt(prompts):
    openai.api_key = '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'
    for prompt in prompts:
        completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", 
        messages=[
            {"role": "user", "content": "{prompt}".format(prompt= prompt)},
            # {"role": "user", "content": "In what situation this synthesized code can be used?"},
                ]
        )
        print(completion)
        time.sleep(30)


def get_synthesized_pattern(center_cluster_1, center_cluster_2):
    openai.api_key = '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'

    completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo", 
    messages=[
        {"role": "user", "content": "Code fragment 1 [{center_cluster_1}] and Code fragment 2 [{center_cluster_2}] synthesize the reasonable code fragment []".format(center_cluster_1= center_cluster_1, center_cluster_2 = center_cluster_2)},
        # {"role": "user", "content": "In what situation this synthesized code can be used?"},
              ]
    )
    print(completion) 
    time.sleep(30) 
    return completion

def whether_a_code_pattern(completion_answer):
    openai.api_key = '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'
    # code = completion_answer['choices'][0]['message']['content']
    code = completion_answer
    completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo", 
    messages=[
        {"role": "user", "content": "Does this synthesized code [{pattern}] possess clear semantics? Please begin the answer with yes or no and explain why".format(pattern= code)},
              ]
    )
    print(completion) 
    time.sleep(30) 
    return completion

def used_pattern_libraries(completion_answer):
    openai.api_key = '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'
    # code = completion_answer['choices'][0]['message']['content']
    code = completion_answer
    completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo", 
    messages=[
        {"role": "user", "content": "What common Java libraires occur the code fragments that are similar to the synthesized code [{pattern}], please give the specific name of these libraries".format(pattern= code)},
              ]
    )
    print(completion)  
    time.sleep(30)
    return completion

def situation_suggestion(completion_answer):
    openai.api_key = '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'
    # code = completion_answer['choices'][0]['message']['content']
    code = completion_answer
    completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo", 
    messages=[
        {"role": "user", "content": "Would this synthesized code [{pattern}] be suitable for use in a general application or common situation? If yes, please describe what application usage this code fragment can be applied. Please begin the answer with yes or no and explain why".format(pattern= code)},
              ]
    )
    print(completion)  
    time.sleep(30)
    return completion

def final_qustion(completion_answer):
    openai.api_key = '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'
    # code = completion_answer['choices'][0]['message']['content']
    code = completion_answer
    completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo", 
    messages=[
        {"role": "user", "content": " [{pattern}] can be considered a common coding pattern or code idiom? Please begin the answer with yes or no and explain why".format(pattern= code)},
              ]
    )
    print(completion) 
    time.sleep(30) 
    return completion


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='args description')
    parser.add_argument('--cluster_data_file', '-cdf', help='the input file')
    parser.add_argument('--completion_result_file', '-crf', help='new file path')
    parser.add_argument('--completion_result_file_single', '-crfs', help='new file path')
    args = parser.parse_args()
    
    # cluster_data_file = r'cluster_data.pkl'
    # completion_result_file = 'completion_result_'
    # completion_result_file_single = r'completion_result.pkl'
    get_pattern_result(args.cluster_data_file, prompts, args.completion_result_file, args.completion_result_file_single, k=3)
