## IdioMine

### 1. We would like to detail the organization of our replicated package.

Our replicated package consists of six folders that organize the relevant data as follows:
      - `Source_code_for_IdioMine` contains the source code of our approach.

      - `Evaluation` contains the code utilized to evaluate the effectiveness of IdioMine in answering RQ1.

      - `Extracted_Idioms` contains IdioMine's extracted idioms.

      - `User_study` contains the top-18 idioms extracted by IdioMine, Haggies, and ChatGPT 3.5, respectively, and users' preference towards those top idioms.
      
      - `RQ3` presents the statistical results of the idioms extracted by IdioMine from various Java projects and libraries.

      - `ChatGPT_results` includes the idioms extracted from different Java projects and libraries by ChatGPT 3.5, as well as those extracted by ChatGPT 4.0 from libraries. These idioms are discussed in Section V.

### 2. we would like to illustrate how to use IdioMine to extract idioms from the source code.

IdioMine includes three steps to extract idioms from datasets.
      - First, IdioMine extracts raw functions from datasets.

            *Command: python get_data.py --PathStr ProjectFolder/LibraryFolder --dataFilePath dataset.pkl*

      - Second, IdioMine constructs DvCFG based on data flow and control flow of source code.

            *Command: python sub_graph.py --dataFilePath dataset.pkl --all_func_info_path DvCFG.pkl*

      - Third, IdioMine extracts DCCs from DvCFG and transforms DCCs into the corresponding code lines.

            *Command: python trans_graph_to_code.py --all_func_info_path DvCFG.pkl --new_file_path sub-idioms.pkl*

      - Then, IdioMine clusters frequent ones from sub-idioms.

            *Command: python frequent_sub_idioms.py sub-idioms.pkl, -> frequent_sub_idioms.pkl*

      - Finally, IdioMine synthesizes related frequent sub-idioms into potential code idioms and identify real idioms from potential ones.
      
            *Command: python ChatGPT_genrate_code_pattern.py --cluster_data_file frequent_sub_idioms.pkl --completion_result_file completion_result_ --completion_result_file_single completion_result.pkl*

