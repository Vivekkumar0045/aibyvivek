# Modules ----------------------------------------------------------------------------------------------------------------------------------
import PyPDF2
import os
import google.generativeai as genai
import time
import ast
import streamlit as st
import shutil

# Gemini-API Inititialization -----------------------------------------------------------------------------------------------------------------------

GOOGLE_API_KEY = 'AIzaSyB2sW7s6q5rSCY5FBOTCrvjJZM2E2SHTds'
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest")
model2 = genai.GenerativeModel(model_name="gemini-2.0-flash")

# Functions Defined ---------------------------------------------------------------------------------------------------------------------

def split_pdf(input_pdf,folder_name):
    output_folder = folder_name
    # os.remove("TempFileStorage")
    # time.sleep(1)
    os.makedirs(output_folder, exist_ok=True)
    with open(input_pdf, "rb") as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        total_pages = len(reader.pages)
        if total_pages < 0:
            print("Error: The input PDF must have at least 1 pages.")
            return
        base_name = f"{folder_name}pdf"
        for i in range(0, total_pages, 2):
            writer = PyPDF2.PdfWriter()
            for j in range(2):
                if i + j < total_pages:
                    writer.add_page(reader.pages[i + j])
            output_filename = os.path.join(output_folder, f"{base_name}{(i//2)+1}.pdf")
            with open(output_filename, "wb") as output_pdf:
                writer.write(output_pdf)
            print(f"Created: {output_filename}")
            st.write(f"Uploading {input_pdf} ...")

def text_extract(path):
    sample_file = genai.upload_file(path=path, display_name="screenshot")
    response = model.generate_content([sample_file, "Extract text from the given pdf. Only provide me the text, don't write any other word."])
    print(response.text)
    return response.text

def mainFunction(folder_path,folder_name):
    split_pdf(folder_path,folder_name=folder_name)
    if not os.path.exists(folder_path):
        print("Folder does not exist.")
        return
    folder_path = folder_name
    mainText = ""  
    for filename in sorted(os.listdir(folder_path)):
        file_path = os.path.join(folder_path, filename)
        
        if os.path.isfile(file_path) and filename.lower().endswith(('.pdf')):
            x = text_extract(file_path)
            mainText += x
            print("Processed:", filename)
            st.write("Processing ...")
    
    mainText += "."
    # print(mainText)
    if(folder_name=="TempAnsFolder"):
        Dict = ans_text_process(mainText)
        return Dict
    if(folder_name=="TempQuesFolder"):
        Dict = qs_text_process(mainText)
        return Dict

def ans_text_process(text):
    response = model.generate_content( 
        text + 
    '''
    
    
    make this in form of a dictionary where key is question number.
    Do not leave any line of the answer as answers may be multiline.
    
    only provide the dictionary nothing else

    ''')   
    response_text = response.text  
    n = len(response_text)
    lower_limit = response_text.find("{")
    upper_limit = response_text.rfind("}")
    if lower_limit == -1 or upper_limit == -1:
        print("Error: No dictionary found in response.")
        return None
    output = response_text[lower_limit:upper_limit+1]
    final_dict1 = ast.literal_eval(output)
    final_dict = convert_dict_to_str(final_dict1)
    # print(final_dict)
    # print(output) 
    return final_dict

def qs_text_process(text):
    response = model.generate_content(
        text + 
        '''


        Extract only the questions from the given text and format them in a dictionary where the key is the question number and the value is the question. 
        Do not include any answers. 

        Only provide the dictionary, nothing else."
        ''')   
    response_text = response.text  
    n = len(response_text)
    lower_limit = response_text.find("{")
    upper_limit = response_text.rfind("}")
    if lower_limit == -1 or upper_limit == -1:
        print("Error: No dictionary found in response.")
        return None
    output = response_text[lower_limit:upper_limit+1]
    final_dict1 = ast.literal_eval(output)
    final_dict = convert_dict_to_str(final_dict1)
    # print(final_dict)
    # print(output) 
    return final_dict

def marks_text_process(path):
    sample_file = genai.upload_file(path=path, display_name="pdf")
    response = model.generate_content([sample_file,
     '''
     

     Extract marks fron given pdf and put it in a python dictionary.

     example of such dictionary - 
    { 1: 3, 2: 5, 3: 3, 4: 3, 5: 5, 6: 3, 7: 10, 8: 3} 
    here keys are question numbers and values are extracted marks

     Note - marks may be or may not be  given next to questions in form of simple numbers carefully extract . 
     don't write any other word than the dictionary **. 
     '''
     ])
    response_text = response.text  
    
    print(response.text)
    n = len(response_text)
    lower_limit = response_text.find("{")
    upper_limit = response_text.rfind("}")
    if lower_limit == -1 or upper_limit == -1:
        print("Error: No dictionary found in response.")
        return None
    output = response_text[lower_limit:upper_limit+1]
    final_dict1 = ast.literal_eval(output)
    final_dict = convert_dict_to_str(final_dict1)
    return final_dict

def convert_dict_values_to_int(input_dict):
    return {key: int(value) if str(value).isdigit() else 0 for key, value in input_dict.items()}

def convert_dict_to_str(input_dict):
    return {str(key): str(value) for key, value in input_dict.items()}

def save_uploaded_file(uploaded_file, filename):
    """Save uploaded file permanently in the uploads folder."""
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def start(answerpath,quespath):
    ans = mainFunction(answerpath,"TempAnsFolder")
    ques = mainFunction(quespath,"TempQuesFolder")
    full_marks = marks_text_process(quespath)
    marks_obtained = {key: "NA" for key in full_marks}
    # marks_obtained = convert_dict_to_str()
    st.write("-----------------------LOGS ENDED------------------------------")
    for key in ques:  
        key_str = str(key)  
        if key_str in ans:  
            q = ques[key]  
            a = ans[key_str]  
            # print(q, "\n\n", a, "\n\n")
            st.write("Question :")
            st.write(q)
            st.write("Answer :")
            st.write(a)
            response = model2.generate_content(
                    [f'''Question : 
                        {q}

                        Answer : 
                        {a}

                        Check whether the answer is correct for given question . Give marks out of {full_marks[key]}.
                        give me the marks in the format - ///marks=marksobtained/// 
                        dont provide me anything other than this given format

                    ''']

                    )
            data_string = response.text.strip("/") 
            _, marks_value = data_string.split("=") 
            marks_value = marks_value.strip("///\n")  
            marks_obtained[key] = int(marks_value) if marks_value.isdigit() else marks_value
            st.write("Marks Obtained :")
            st.write(marks_obtained[key])
            st.write("Full Marks :")
            st.write(full_marks[key])
            st.write("  ")
        else:
            # print(f"{key}: Key does not exist., 0 Marks")
            qu = ques[key]
            st.write("Question :")
            st.write(qu)
            st.write("Answer :")
            st.write("Question Not Attempted by Candidate ")
            st.write("Marks Obtained :")
            st.write("0")
            st.write("Full Marks :")
            st.write(full_marks[key])
            st.write("  ")
            
            continue
    # dictt = convert_dict_values_to_int(marks_obtained)  
    # print(dictt)
    print(marks_obtained)
    # st.write(dictt)
    print(full_marks)

# Usage  ------------------------------------------------------------------------------------------------------------------------------------

# start("answers2.pdf" , "Question.pdf")

UPLOAD_FOLDER = "uploads" 
os.makedirs(UPLOAD_FOLDER, exist_ok=True) 

def main():
    st.title("AI ASSIGNMENT CHECKER - GDSC")
    st.write("Upload two PDFs: one for answers and one for questions.")
    
    answer_file = st.file_uploader("Upload Answers PDF", type=["pdf"])
    question_file = st.file_uploader("Upload Questions PDF", type=["pdf"])
    st.write("-----------------------LOGS------------------------------")
    if answer_file and question_file:
        ans_path = save_uploaded_file(answer_file, "answers.pdf")
        ques_path = save_uploaded_file(question_file, "questions.pdf")

        st.success(f"Files saved  in Dir -- `{UPLOAD_FOLDER}/`")
        st.write("Processing files...")
        
        start(ans_path, ques_path)
        shutil.rmtree("TempAnsFolder")
        shutil.rmtree("TempQuesFolder")
        shutil.rmtree("uploads")

if __name__ == "__main__":
    main()



