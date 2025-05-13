import streamlit as st
from ..Requirements_scripts.utility import create_folder,extract_folders,split_folders_titles, Next_Orphan_foldername, extract_titles
from ..Requirements_scripts.TestCase import TestCaseDataRet
import os
import datetime
import sys
from ..Requirements_scripts.Analytics import Analytics
from .feedback import feedback_dialog
from .common_style import apply_default_button_styles
from bs4 import BeautifulSoup

current_dir = os.path.dirname(os.path.abspath(__file__))
three_dirs_up = os.path.abspath(os.path.join(current_dir, "../../.."))
sys.path.insert(0, three_dirs_up)
from common_rag_utility import *
from ADO_scripts.Get_WorkItem import *

user_story_dict = {}
Userstory_titles = []
test_case_dict = {}  # Dictionary to store test cases
test_case_titles = []  # List to store test case titles
test_case_save_button_key = 'tc_save_button_clicked'
"""
    Load user stories based on the current session state and configuration.

    This function retrieves user stories from a specified project, team, and iteration. It logs the process 
    if logging is enabled for the current page. The user stories are returned in a dictionary format for easy 
    access and a list of titles for display purposes.

    Parameters:
        session_states (dict): A dictionary containing the current session's state and configuration, including 
                               organization name, selected project, team, iteration, and logger configuration.

    Returns:
        tuple: A dictionary of user stories where each key is the story title and the value is another dictionary 
               containing the story's ID, description, acceptance criteria, and demo information, and a list of 
               titles of the user stories.
"""
def load_user_stories(session_states):
    page_name = 'User Story'
    loggerConfig_object = session_states[LOGGERCONFIG_OBJECT]
    page = session_states[CURRENT_UI_PAGE]
    
    #Verifying page log flag is enabled or not
    if verify_log_variable(page, loggerConfig_object):
        # log_writer(session_states['log_file_descriptor'], page, "save_settings function started")
        logger.info(f"{page} load_user_stories function Started")

    try:
        # Retrieve the list of user stories from the specified organization, project, team, and iteration
        user_stories_list = get_user_stories(session_states[CONST_ENTER_ORG_NAME], session_states[CONST_SEL_PROJECT],
                                             session_states[CONST_SEL_STEAM], session_states[CONST_SEL_SITERATION], page_name, session_states)
        # Check if the retrieved user stories are in list format
        if isinstance(user_stories_list, list):
            FT = []    
            user_story_dict = {}
            for story in user_stories_list:
                sList = str(story['ID']) + '~' + story['Title']
                FT.append(sList)
                user_story_dict[story['ID']] = {
                    "Description": story['Description'],
                    "AcceptanceCriteria": story['AcceptanceCriteria'],
                    "Howtodemo": story['Howtodemo'],
                    "AdditionalInfo": story['AdditionalInfo']
                }
            if verify_log_variable(page, loggerConfig_object):
                # log_writer(session_states['log_file_descriptor'], page, "save_settings function started")
                logger.info(f"{page} load_user_stories function Ended")
            return user_story_dict, FT
        else:
            # Handle the case where the return value is not a list
            return {}, []  # or return an error message depending on your design    
    except KeyError as e:
        st.toast(f"Key error: {e}. Please check the session state keys.")
        if verify_log_variable(page, loggerConfig_object):
            logger.error(f"{page} Key error: {e}. Please check the session state keys.")
        return {}, []  # Return empty structures on error    
    except TypeError as type_err:
        if verify_log_variable(page, loggerConfig_object):
            logger.error(f"{page} Type error occurred: {type_err}")
        st.toast(f"Type error occurred: {type_err}")
        return {}, []    
    except Exception as e:
        if verify_log_variable(page, loggerConfig_object):
            logger.error(f"{page} An error occurred while loading user stories: {e}")
        st.toast(f"An error occurred while loading user stories: {e}")
        return {}, []  # Return empty structures on error
    
#Create a text area with a toggle button to enable/disable it and store its value in session states.
def create_text_area(label, value, toggle_button):    
    # Create a toggle button to enable or disable the text area
    #toggle_button = st.checkbox(f"{label}:", value=True)  # Default to enabled
    
    if f"{label}_value" not in st.session_state:
        st.session_state[f"{label}_value"] = value
    if st.session_state["curr_workitem_ID"] != st.session_state["prev_workitem_ID"]:
        del st.session_state[f"{label}_value"]
        del st.session_state[f"Recreate_{label}"]
        st.session_state[f"{label}_value"] = value
        #Description_value, Acceptance_Criteria_value, How_to_Demo_value, Additional_Information_value

    # Create the text area; enable or disable based on the toggle button
    # text_area_value = st.text_area(
    #     label=label+" (AI-Generated Content)",
    #     key=f"{label}_text_area",
    #     #label_visibility="hidden",
    #     height=150,
    #     value=st.session_state[f"{label}_value"],
    #     disabled=not toggle_button  # Disable if toggle is off
    # )
    text_area_value = value
    st.session_state[f"{label}_value"] = text_area_value
    return text_area_value, toggle_button

#Function to save the response
def finalize_data(page,foldername,data,option,session_states):
    page = session_states[CURRENT_UI_PAGE]
    LoggerObject = session_states[LOGGERCONFIG_OBJECT]
    if verify_log_variable(page, LoggerObject):
        # log_writer(session_states['log_file_descriptor'], page, "load_examples function started")
        logger.info(f"{page} finalize_data function Started")

    try:
        destination_path = session_states[CONST_TESTCASE_FINALIZED_PATH]
        path = create_folder(destination_path,foldername,page,data,session_states)
        #Declaring session state flag for the radio selected to one
        session_states[option]=1

        if verify_log_variable(page, LoggerObject):
            # log_writer(session_states['log_file_descriptor'], page, "load_examples function started")
            logger.info(f"{page} finalize_data function Ended")
    except Exception as e:
        error_msg = handle_exception(e)
        st.toast(error_msg)
        if verify_log_variable(page, LoggerObject):
            # log_writer(session_states['log_file_descriptor'], page, "load_examples function started")
            logger.error(f"{page} {error_msg}")

#Declaring session state flags for every radio in the list to zero.
def radio_change(radios,session_states):
    for radio in radios:
        if(radio not in session_states):
            session_states[radio]=0

#Function to create and recreate the response
def create_response(Acceptance_criteria_title,UserStory_title,session_states,recreate_flag):
    page = session_states[CURRENT_UI_PAGE]
    LoggerObject = session_states[LOGGERCONFIG_OBJECT]
    if verify_log_variable(page, LoggerObject):
        # log_writer(session_states['log_file_descriptor'], page, "load_examples function started")
        logger.info(f"{page} create_response function Started")
    try:
        temperature=session_states[CONST_TEMPERATURE]
        prompt=session_states[CONST_TESTCASE_USER_TEXT]
        template=session_states[CONST_TESTCASE_USER_TEMPLATE]
        example=session_states[CONST_TESTCASE_USER_EXAMPLE]

        if template == '' or template == 'None':
            template=session_states[CONST_PROMPT_DICTIONARY][CONST_TESTCASE_DEFAULT_TEMPLATE]

        if(UserStory_title =='Create new Test Case'):
            if prompt=='' or prompt=='None':
                if Acceptance_criteria_title == '':
                    dictionary_prompt = session_states[CONST_PROMPT_DICTIONARY][CONST_TESTCASE_CNP_WITHOUTUSERINPUT]
                else:
                    dictionary_prompt = session_states[CONST_PROMPT_DICTIONARY][CONST_TESTCASE_DEFAULT_PROMPT]
            else:
                if Acceptance_criteria_title == '':
                    dictionary_prompt = session_states[CONST_PROMPT_DICTIONARY][CONST_TESTCASE_CREATE_NEW_PROMPT]
                else:
                    dictionary_prompt = session_states[CONST_PROMPT_DICTIONARY][CONST_TESTCASE_DEFAULT_PROMPT]
            response = TestCaseDataRet(prompt,template,example,
                                session_states[CONST_DEFAULT_FOLDER],'',Acceptance_criteria_title,
                                session_states[CONST_CONTENT],
                                dictionary_prompt, session_states,recreate_flag, temperature)

            if response[1]!='':
                # We are extracting TestCase title from the TestCase output document to const Acceptance criteria option
                session_states[CONST_ACCEPTANCE_CRITERIA_OPTION] = extract_titles(response[1],session_states,0)[0]
            else:
                session_states[CONST_ACCEPTANCE_CRITERIA_OPTION] = ''

            #Intialize the session_states[CONST_USERSTORY_OPTION]
            # session_states[session_states[CONST_USERSTORY_OPTION]] = 2

            if(response[2]!=''):
                session_states[session_states[CONST_ACCEPTANCE_CRITERIA_OPTION]+'data'] = response[2]
                session_states[CONST_CREATE_NEW_TESTCASE_STATUS] = True
            else:
                session_states[session_states[CONST_ACCEPTANCE_CRITERIA_OPTION]+'data'] = response[0]
                session_states[CONST_CREATE_NEW_TESTCASE_STATUS] = False
        else:
            response = TestCaseDataRet(prompt,template,example,
                                    session_states[CONST_DEFAULT_FOLDER],UserStory_title,Acceptance_criteria_title,session_states[CONST_CONTENT],
                                    session_states[CONST_PROMPT_DICTIONARY][CONST_TESTCASE_DEFAULT_PROMPT],
                                    session_states,recreate_flag, temperature)

            #We are getting data, filepath and error message in a list. Using them in below variables. As filepath is not required for now because we have acceptance criteria title, no need to extract from output docx.    
            session_states[Acceptance_criteria_title+'data']=response[0]
        
        if(response[2]=='No_RAG'):
            session_states[page+'_enable'] = 3
        elif(response[2]!=''):
            st.toast(response[2])
            response = []

        if verify_log_variable(page, LoggerObject):
            # log_writer(session_states['log_file_descriptor'], page, "load_examples function started")
            logger.info(f"{page} create_response function Ended")

    except Exception as e:
        error_msg = handle_exception(e)
        st.toast(error_msg)
        if verify_log_variable(page, LoggerObject):
            # log_writer(session_states['log_file_descriptor'], page, "load_examples function started")
            logger.error(f"{page} {error_msg}")
#Userstory UI Page function
@st.experimental_fragment
def main_page(session_states):
    apply_default_button_styles()
    session_states[CURRENT_UI_PAGE] = page = CONST_TESTCASE_PAGE
    LoggerObject = session_states[LOGGERCONFIG_OBJECT]
    if verify_log_variable(page, LoggerObject):
        # log_writer(session_states['log_file_descriptor'], page, "load_examples function started")
        logger.info(f"{page} {page} UI page Started")
    try:
        
        if test_case_save_button_key not in session_states:
            session_states[test_case_save_button_key] = False
        
        # If 'selected_test_case_id' not in session state, initialize it
        if 'selected_test_case_id' not in session_states:
            session_states['selected_test_case_id'] = None
        
        page_foldername='TestCases'
        default_path=session_states[CONST_DEFAULT_FOLDER]
        UserStory_folder_titles = []

        # Path to storage file
        TestCase_path = os.path.join(default_path, page_foldername)
        storage_file = os.path.join(TestCase_path, 'customize_settings_TestCase.txt')
    
        # Read stored values
        stored_user_input, stored_template, stored_example = read_storage(storage_file, session_states)

        #Defining session states to store customize inputs
        if TESTCASE_UNIQUE_KEY not in session_states:
            session_states[TESTCASE_UNIQUE_KEY]='4'
        if CONST_TESTCASE_USER_TEXT not in session_states:
            session_states[CONST_TESTCASE_USER_TEXT]=stored_user_input
        if CONST_TESTCASE_USER_TEMPLATE not in session_states:
            if stored_template != '' and stored_template != 'None':
                template_path=os.path.join(default_path,page_foldername,'Templates',stored_template)
                extension=os.path.splitext(stored_template)[1]
                session_states[CONST_TESTCASE_USER_TEMPLATE]= extract_data_from_text_pdf_docx_files(template_path,extension, session_states)
            else:            
                session_states[CONST_TESTCASE_USER_TEMPLATE]= ""
        if CONST_TESTCASE_USER_EXAMPLE not in session_states:
            if stored_example != '' and stored_example != 'None':
                example_path=os.path.join(default_path,page_foldername,'Examples',stored_example)
                extension=os.path.splitext(stored_example)[1]
                session_states[CONST_TESTCASE_USER_EXAMPLE] = extract_data_from_text_pdf_docx_files(example_path,extension, session_states)
            else:            
                session_states[CONST_TESTCASE_USER_EXAMPLE]= ""
        if TESTCASE_SELECTED_TEMPLATE not in session_states:
            session_states[TESTCASE_SELECTED_TEMPLATE]=stored_template
        if TESTCASE_SELECTED_EXAMPLE not in session_states:
            session_states[TESTCASE_SELECTED_EXAMPLE]=stored_example
            
        if CONST_TESTCASE_FOLDERNAME not in session_states:
            session_states[CONST_TESTCASE_FOLDERNAME] = ""

        # This flag is set to prevent the prompt output from being created multiple times.
        # Setting session_states[CONST_CREATE_NEW_FLAG] to 0 to Initialize
        # and 1 indicates that the output should not be generated repeatedly.
        if CONST_CREATE_NEW_TESTCASE_FLAG not in session_states:
            session_states[CONST_CREATE_NEW_TESTCASE_FLAG]=0

        #option is setting in session state
        if CONST_ACCEPTANCE_CRITERIA_OPTION not in session_states:
            session_states[CONST_ACCEPTANCE_CRITERIA_OPTION]=''

        #Creating three columns and using customize in column1 only. column2,column3 aren't used but they are required.
        column1, column2, column3 = st.columns(3)
        global user_story_dict, Userstory_titles, test_case_dict, test_case_titles
        
        with column3:
            TESTCASE_ADO_TOGGLE = "testcase_ado_toggle"  # Define the variable
            if TESTCASE_ADO_TOGGLE not in session_states:
                session_states[TESTCASE_ADO_TOGGLE] = False
            
            session_states[TESTCASE_ADO_TOGGLE] = st.toggle("ADO", value=session_states[TESTCASE_ADO_TOGGLE], key="testcase_toggle")

            global user_story_dict, Userstory_titles, test_case_dict, test_case_titles
            if not session_states[TESTCASE_ADO_TOGGLE]:
                Userstory_titles = []
                user_story_dict = {}
                test_case_titles = []
                test_case_dict = {}
                Userstory_titles.append('Create new Test Case')
            else:
                user_story_dict, Userstory_titles = load_user_stories(session_states)
                test_case_dict, test_case_titles = load_test_cases(session_states)  
        with column1:
            with st.popover("Customize"):

                #Assigning unique key
                unique_key=session_states[TESTCASE_UNIQUE_KEY]
                time=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                TestCase_user_text=''
                TestCase_user_template=''
                TestCase_user_example=''

                TestCase_user_text = st.text_area("Provide an Input to Shape TC Outcomes", value=session_states[CONST_TESTCASE_USER_TEXT], key = 'prompt_us'+unique_key)

                #Retrieving all files in Templates folder
                
                templates = os.listdir(os.path.join(default_path,page_foldername,'Templates'))
                templates = [file for file in templates if file.endswith(('.pdf', '.txt', '.docx'))]
                templates.append('None')

                # If there are templates
                if templates:
                    try:
                        selected_template = st.selectbox("Select a template to structure the TC:", templates, index=len(templates) - 1 if stored_template == "" else templates.index(stored_template), key='template_us'+unique_key)
                        if (selected_template!=None and selected_template!='None'):
                            template_path=os.path.join(default_path,page_foldername,'Templates',selected_template)
                            extension=os.path.splitext(template_path)[1]
                            TestCase_user_template=extract_data_from_text_pdf_docx_files(template_path,extension, session_states)
                    except ValueError:
                        st.toast(f'The selected Template "{stored_template}" is not present in the directory.')
                        if verify_log_variable(page, LoggerObject):
                            # log_writer(session_states['log_file_descriptor'], page, "load_examples function started")
                            logger.error(f"{page} The Selected Template {stored_template} is not present in the directory.")
                        
                        # selected_template=None

                #Retrieving all files in Examples folder 
                examples = os.listdir(os.path.join(default_path,page_foldername,'Examples'))
                examples = [file for file in examples if file.endswith(('.pdf', '.txt', '.docx'))]
                examples.append('None')

                # If there are examples
                if examples:
                    try:
                        selected_example = st.selectbox("Select an example to structure the TC:", examples, index=len(examples) - 1 if stored_example == "" else examples.index(stored_example), key='example_us'+unique_key)
                        if (selected_example != None and selected_example != 'None'):
                            example_path=os.path.join(default_path,page_foldername,'Examples',selected_example)
                            extension=os.path.splitext(example_path)[1]
                            TestCase_user_example=extract_data_from_text_pdf_docx_files(example_path,extension, session_states)
                    except ValueError:
                        st.toast(f'The selected Example "{stored_example}" is not present in the directory.')
                        if verify_log_variable(page, LoggerObject):
                            # log_writer(session_states['log_file_descriptor'], page, "load_examples function started")
                            logger.error(f"{page} The Selected Example {stored_example} is not present in the directory.")
                        # selected_example=None

                # On Apply, custom values are stored in session state
                if st.button('Apply'):
                    st.write('Applied')
                    session_states[CONST_TESTCASE_USER_TEXT] = TestCase_user_text
                    session_states[CONST_TESTCASE_USER_TEMPLATE] = TestCase_user_template
                    session_states[CONST_TESTCASE_USER_EXAMPLE] = TestCase_user_example
                    session_states[TESTCASE_SELECTED_TEMPLATE] = selected_template
                    session_states[TESTCASE_SELECTED_EXAMPLE] = selected_example
                        
                    if TestCase_user_text is None:
                        session_states[CONST_TESTCASE_USER_TEXT] = ""
                    if TestCase_user_template is None:
                        session_states[CONST_TESTCASE_USER_TEMPLATE] = "None"
                    if TestCase_user_example is None:
                        session_states[CONST_TESTCASE_USER_EXAMPLE] = "None"
                    if selected_template is None:
                        session_states[TESTCASE_SELECTED_TEMPLATE] = 'None'
                    if selected_example is None:
                        session_states[TESTCASE_SELECTED_EXAMPLE] = 'None'

                    # Store the current values to storage file
                    write_storage(storage_file, session_states[CONST_TESTCASE_USER_TEXT], session_states[TESTCASE_SELECTED_TEMPLATE], session_states[TESTCASE_SELECTED_EXAMPLE], session_states)
            #Adding the info button
            tooltip = tooltip_text(session_states)
            # Add a circular button and display the text on hover
            st.markdown(
                f"""
                <div class="info-container">
                    <button class="bubble-button">
                        <i style="font-style: italic; font-family: 'Georgia', 'Times New Roman', 'Cursive', sans-serif;">i</i>
                    </button>
                    <div class="info-text">{tooltip['Test Case Page Info']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        page=CONST_TESTCASE_PAGE
        # st.subheader(page)

        #Adding note if database is not there
        if(not(is_db_exists(default_path))):
            st.write("Note: No contextual database and/or user prompt detected. Providing both will enhance the accuracy of the output.")
        st.subheader(page)

        if(session_states[page+"_enable"]==1):
            if(is_db_exists(default_path)):
                #Summarizing the content and storing in a session state, which is used as content. 
                with st.spinner('Loading the Test Case Page....'):
                    summary_status=summary(session_states)
                if(summary_status!=''):
                    st.toast(summary_status)
            else:
                session_states['ingest']=2
                session_states[CONST_CONTENT]=''
            session_states[page+"_enable"]=2
        if(session_states[page+"_enable"]==2):

            #Accessing UserStory folders and Epic titles in a list
            UserStory_folder_titles=extract_folders(session_states[CONST_USERSTORY_FINALIZED_PATH],CONST_USERSTORY_PAGE,session_states,0)

            #Accessing Userstory foldernames and titles from UserStoryList document
            TestCase_folder_titles=extract_folders(session_states[CONST_USERSTORY_FINALIZED_PATH],CONST_USERSTORY_PAGE,session_states,1)
            #UserStory_folders=split_folders_titles(UserStory_folder_titles,0)

            #Separating folders and UserStory titles
            UserStory_titles_unprocessed=split_folders_titles(UserStory_folder_titles,session_states,1)

            #Processed Userstory titles
            Acceptance_criteria_titles=split_folders_titles(TestCase_folder_titles,session_states,1)
            UserStory_titles=[]
            for item in UserStory_titles_unprocessed:
                UserStory_titles.append(item[0])
            folders=[]
            titles=[]

            #Adding Create new to UserStory_titles
            UserStory_titles.append('Create new Test Case')
            #----------------------------------------------
            if not session_states[TESTCASE_ADO_TOGGLE]:
                Userstory_titles=[]
                for item in UserStory_titles_unprocessed:
                    Userstory_titles.append(item[0])
                #Adding Create new to Feature_titles
                Userstory_titles.append('Create new User Story')              
            folders=[]
            titles=[]

            if session_states[TESTCASE_ADO_TOGGLE]:
                tab1, tab2, tab3 = st.tabs([":mag: Enhance Existing Test Case", ":magic_wand: Create Test Case from User Story", ":star: Create New Test Case"])
                
                with tab1:
                    st.subheader("Enhance Existing Test Cases")
                    
                    # Display a selectbox with test case titles from ADO
                    organization_name = session_states[CONST_ENTER_ORG_NAME]
                    project = session_states[CONST_SEL_PROJECT]
                    iteration = session_states[CONST_SEL_SITERATION]
                    
                    if organization_name:
                        test_case_title = st.selectbox(
                            f"Select a Test Case from ADO Iteration Path: {organization_name}\\{project}\\{iteration}", 
                            test_case_titles, 
                            index=None,
                            key="test_case_selectbox_from_ADO"
                        )
                    else:
                        test_case_title = st.selectbox(
                            f"Select a Test Case from ADO Iteration Path:", 
                            test_case_titles,
                            index=None,
                            key="test_case_selectbox_from_ADO"
                        )
                        st.toast("Error: The organization could not be found, or you do not have access to it. Please verify in settings page")
                    
                    if test_case_title:
                        # Extract test case ID from the selected title (format: "ID~Title")
                        test_case_id = int(test_case_title.split('~')[0])
                        session_states['selected_test_case_id'] = test_case_id
                        
                        # Get the selected test case details
                        selected_test_case = test_case_dict[test_case_id]
                        
                        # Display test case details
                        st.write(f"**ID:** {test_case_id}")
                        st.write(f"**Title:** {selected_test_case['Title']}")
                        
                        # Track current and previous test case IDs
                        if "curr_test_case_ID" in session_states:
                            session_states["prev_test_case_ID"] = session_states["curr_test_case_ID"]
                        
                        session_states["curr_test_case_ID"] = test_case_id
                        if "prev_test_case_ID" not in session_states:
                            session_states["prev_test_case_ID"] = test_case_id
                        
                        # Reset recreation flags if a different test case is selected
                        if session_states["prev_test_case_ID"] != session_states["curr_test_case_ID"]:
                            session_states["Recreate_TestCase"] = False
                            session_states["Push_to_UpdateADO_flag"] = True
                        
                        # Default set to False if not exists
                        if "Recreate_TestCase" not in session_states:
                            session_states["Recreate_TestCase"] = False
                        
                        # Create expandable sections for test case details
                        with st.expander("View Test Case Details", expanded=True):
                            st.markdown("### Pre-Conditions")
                            st.write(selected_test_case['PreConditions'])
                            
                            st.markdown("### Steps")
                            st.write(selected_test_case['Steps'])
                            
                            st.markdown("### Expected Results")
                            st.write(selected_test_case['ExpectedResults'])
                            
                            if selected_test_case['AdditionalInfo']:
                                st.markdown("### Additional Information")
                                st.write(selected_test_case['AdditionalInfo'])
                        
                        # Key for tracking if this test case has been enhanced
                        enhanced_key = f"enhanced_test_case_{test_case_id}"
                        
                        # If enhanced content exists, show it
                        if enhanced_key in session_states:
                            with st.expander("Enhanced Test Case", expanded=True):
                                session_states[f"{enhanced_key}_text"] = st.text_area(
                                    "Enhanced content",
                                    value=session_states[enhanced_key],
                                    height=400,
                                    key=f"enhanced_display_{test_case_id}"
                                )
                        
                        # Create buttons for enhancing and pushing to ADO
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            recreate_button = st.button("Recreate/Enhance", key="enhance_button")
                            if recreate_button:
                                with st.spinner("Enhancing test case, please wait..."):
                                    session_states["Recreate_TestCase"] = True
                                    
                                    # Format the test case content
                                    test_case_content = (
                                        f"Title: {selected_test_case['Title']}\n"
                                        f"Pre-Conditions: {selected_test_case['PreConditions']}\n"
                                        f"Steps: {selected_test_case['Steps']}\n"
                                        f"Expected Results: {selected_test_case['ExpectedResults']}\n"
                                        f"Additional Information: {selected_test_case['AdditionalInfo']}\n"
                                    )
                                    
                                    # Enhance the test case
                                    enhanced_content = enhance_test_case(test_case_content, session_states, 1)
                                    
                                    # Store in session state
                                    session_states[enhanced_key] = enhanced_content
                                    
                                    # Check if template and example allow pushing to ADO
                                    template = session_states[CONST_TESTCASE_USER_TEMPLATE]
                                    example = session_states[CONST_TESTCASE_USER_EXAMPLE]
                                    
                                    if (template == '' or template == 'None') and (example == '' or example == 'None'):
                                        session_states["Push_to_UpdateADO_flag"] = True
                                    else:
                                        session_states["Push_to_UpdateADO_flag"] = False
                                    
                                    # Log analytics
                                    analytics = Analytics(default_path, session_states.username)
                                    analytics.write_analytics(
                                        CONST_TESTCASE_PAGE, 
                                        str(test_case_id), 
                                        "ADO-Enhance", 
                                        organization_name, 
                                        project, 
                                        iteration
                                    )
                        
                        with col2:
                            # Only show push button if enhanced version exists and pushing is allowed
                            if enhanced_key in session_states:
                                if session_states["Push_to_UpdateADO_flag"]:
                                    push_button = st.button("Push to ADO", key="push_to_ado_button")
                                    if push_button:
                                        with st.spinner("Pushing test case to ADO, please wait..."):
                                            # Get the latest content from the text area
                                            if f"{enhanced_key}_text" in session_states:
                                                content_to_push = session_states[f"{enhanced_key}_text"]
                                            else:
                                                content_to_push = session_states[enhanced_key]
                                                
                                            # Update test case in ADO
                                            error_msg = update_test_case_in_ado(
                                                session_states, 
                                                test_case_id, 
                                                content_to_push
                                            )
                                            
                                            if error_msg:
                                                st.toast(f"Error updating test case in ADO: {error_msg}")
                                            else:
                                                st.success("Test case successfully pushed to ADO!")
                                                
                                                # Log analytics
                                                analytics = Analytics(default_path, session_states.username)
                                                analytics.write_analytics(
                                                    CONST_TESTCASE_PAGE, 
                                                    str(test_case_id), 
                                                    "ADO-Push", 
                                                    organization_name, 
                                                    project, 
                                                    iteration
                                                )
                                else:
                                    st.warning("Push denied. Set template and/or example to None and recreate.")
                
                with tab2:
                    # Selecting a userstory from ADO
                    organization_name = session_states[CONST_ENTER_ORG_NAME]
                    project = session_states[CONST_SEL_PROJECT]
                    team = session_states[CONST_SEL_STEAM]
                    iteration = session_states[CONST_SEL_SITERATION]
                    if organization_name:
                        UserStory_title = st.selectbox(f"Select a Parent User Story from ADO Iteration Path: {organization_name}\\{project}\\{iteration}", Userstory_titles, index=None,key="Userstory_selectbox_from_ADO")
                    else:
                        UserStory_title = st.selectbox(f"Select a Parent User Story from ADO Iteration Path:", Userstory_titles,index=None,key="Userstory_selectbox_from_ADO")
                        st.toast("Error: The organization could not be found, or you do not have access to it. Please verify in settings page")

                    if UserStory_title:
                        workitem_id = UserStory_title.split('~')[0]
                        selected_story = user_story_dict[int(workitem_id)]
                        selected_description = (
                            f"{selected_story['Description']}\n"
                            f"Acceptance Criteria: {selected_story['AcceptanceCriteria']}\n"
                            f"How to Demo: {selected_story['Howtodemo']}\n"
                            f"Additional Information: {selected_story['AdditionalInfo']}\n"
                        )
                        
                        # Replace html text
                        selected_description = selected_description.replace("<br>", "\n")
                        cleaned_text = selected_description

                        # Split the cleaned text into sections
                        Desc=description = cleaned_text.split("Acceptance Criteria:")[0].strip()
                        Accep= acceptance_criteria = cleaned_text.split("Acceptance Criteria:")[1].split("How to Demo:")[0].strip()
                        demo= how_to_demo = cleaned_text.split("How to Demo:")[1].split("Additional Information:")[0].strip()
                        AddInfo= Add_Info = cleaned_text.split("Additional Information:")[1].strip()

                        # Display read-only label with value
                        st.write(f"**ID:** {workitem_id}")
                        if "curr_workitem_ID" in session_states:
                            session_states["prev_workitem_ID"] = st.session_state["curr_workitem_ID"]

                        st.session_state["curr_workitem_ID"] = workitem_id
                        if "prev_workitem_ID" not in st.session_state:
                            session_states["prev_workitem_ID"] = workitem_id

                        if "Push_to_UpdateADO_flag" not in session_states:
                                session_states["Push_to_UpdateADO_flag"] = True 

                        # WorkItem ID's are different    
                        if session_states["prev_workitem_ID"] != st.session_state["curr_workitem_ID"]:
                            session_states["Recreate_Description"] = False
                            session_states["Recreate_Acceptance_Criteria"] = False
                            session_states["Recreate_How_to_Demo"] = False
                            session_states["Recreate_Additional_Information"] = False
                            session_states["Push_to_UpdateADO_flag"] = True 

                        # Default set to False
                        if "Recreate_Description" not in session_states:
                            session_states["Recreate_Description"] = False
                        if "Recreate_Acceptance_Criteria" not in session_states:
                            session_states["Recreate_Acceptance_Criteria"] = False
                        if "Recreate_How_to_Demo" not in session_states:
                            session_states["Recreate_How_to_Demo"] = False
                        if "Recreate_Additional_Information" not in session_states:
                            session_states["Recreate_Additional_Information"] = False

                        # Remove HTML tags from the acceptance criteria
                        # Parse the acceptance criteria into individual points based on <li> tags in HTML
                        soup = BeautifulSoup(acceptance_criteria, 'html.parser')
                        acceptance_criteria_points = [li.get_text(strip=True) for li in soup.find_all('li')]

                        selected_points = []

                        for i, point in enumerate(acceptance_criteria_points):
                            # Render the point as a checkbox
                            if point:
                                is_selected = st.checkbox(f"{i + 1}: {point}", key=f"acceptance_criteria_point_{i}")
                                if is_selected:
                                    selected_points.append(point)
                        
                        # Prepare the acceptance criteria prompt
                        Accep_recreate_prompt = session_states[CONST_PROMPT_DICTIONARY][USERSTORY_DEFAULT_PROMPT_AC]
                        ADOisenabledgetdata = []
                        ADOisenabledgetdata.append({CONST_ACCEPT: Accep_recreate_prompt})

                        create_button = st.button('Create Test Case', key='TESTCASE_ADO_create', help="Create a new test case based on selected Acceptance criteria")
                        if create_button:
                            with st.spinner("Creating test case, please wait..."):
                                session_states[session_states[CONST_ACCEPTANCE_CRITERIA_OPTION]] = 1
                                if selected_points:
                                    Accep = "\n".join(selected_points)
                                    session_states[CONST_ACCEPTANCE_CRITERIA_OPTION] = Accep
                                    create_response(session_states[CONST_ACCEPTANCE_CRITERIA_OPTION], UserStory_title, session_states, 0)
                                    analytics = Analytics(default_path, session_states.username)
                                    analytics.write_analytics(CONST_TESTCASE_PAGE, session_states[CONST_ACCEPTANCE_CRITERIA_OPTION], "ADO-Testcase-Create", session_states[CONST_ENTER_ORG_NAME], session_states[CONST_SEL_PROJECT], session_states[CONST_SEL_SITERATION])
                                    if session_states[page+"_enable"] == 3:
                                            session_states[page+"_enable"] = 1
                                            session_states[CONST_ACCEPTANCE_CRITERIA_OPTION]=None
                                    if(session_states[CONST_ACCEPTANCE_CRITERIA_OPTION]+'data' in session_states):
                                        session_states[session_states[CONST_ACCEPTANCE_CRITERIA_OPTION]+'text']=st.text_area(label=session_states[CONST_ACCEPTANCE_CRITERIA_OPTION],label_visibility="collapsed",height=700,value=session_states[session_states[CONST_ACCEPTANCE_CRITERIA_OPTION]+'data'])
                                else:
                                    st.info("Please select at least one Acceptance Criteria to create the data.")
                
                with tab3:
                    # Create a new test case from scratch
                    st.subheader("Create a New Test Case")
                    
                    # Text field for test case title
                    test_case_title = st.text_input("Test Case Title", key="new_test_case_title")
                    
                    # Text areas for different sections of the test case
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        test_case_preconditions = st.text_area("Pre-Conditions", height=150, key="new_test_case_preconditions")
                        test_case_steps = st.text_area("Steps", height=200, key="new_test_case_steps")
                    
                    with col2:
                        test_case_expected = st.text_area("Expected Results", height=150, key="new_test_case_expected")
                        test_case_additional = st.text_area("Additional Information", height=200, key="new_test_case_additional")
                    
                    # Store the inputs in session state for AI enhancement
                    if "new_test_case_content" not in session_states:
                        session_states["new_test_case_content"] = ""
                    
                    # Button to create the test case
                    create_button = st.button("Generate Test Case", key="create_new_test_case_button")
                    if create_button:
                        if not test_case_title:
                            st.warning("Please provide a title for the test case.")
                        else:
                            with st.spinner("Creating new test case, please wait..."):
                                # Format the test case content
                                test_case_content = (
                                    f"Title: {test_case_title}\n"
                                    f"Pre-Conditions: {test_case_preconditions}\n"
                                    f"Steps: {test_case_steps}\n"
                                    f"Expected Results: {test_case_expected}\n"
                                    f"Additional Information: {test_case_additional}\n"
                                )
                                
                                session_states["new_test_case_content"] = test_case_content
                                
                                # Use the AI to enhance or create the test case
                                session_states[CONST_CREATE_NEW_TESTCASE_FLAG] = 1
                                
                                # Set a placeholder for acceptance criteria option to avoid None errors
                                session_states[CONST_ACCEPTANCE_CRITERIA_OPTION] = "New Test Case"
                                
                                # Create response using the create_response function
                                create_response('', 'Create new Test Case', session_states, 0)
                                
                                # Log analytics
                                analytics = Analytics(default_path, session_states.username)
                                analytics.write_analytics(CONST_TESTCASE_PAGE, "New Test Case", "Create")
                                
                                if session_states[page+"_enable"] == 3:
                                    session_states[page+"_enable"] = 1
                                    session_states[CONST_ACCEPTANCE_CRITERIA_OPTION] = None
                                
                                # Generate a unique folder name for this orphan test case
                                session_states[CONST_TESTCASE_FOLDERNAME] = Next_Orphan_foldername(
                                    session_states[CONST_TESTCASE_FINALIZED_PATH],
                                    CONST_TESTCASE_PAGE,
                                    session_states
                                )
                    
                    # Display the AI-enhanced test case if available
                    if session_states[CONST_ACCEPTANCE_CRITERIA_OPTION] and session_states[CONST_ACCEPTANCE_CRITERIA_OPTION]+'data' in session_states:
                        st.subheader("Generated Test Case")
                        session_states[session_states[CONST_ACCEPTANCE_CRITERIA_OPTION]+'text'] = st.text_area(
                            label="AI-Enhanced Test Case",
                            value=session_states[session_states[CONST_ACCEPTANCE_CRITERIA_OPTION]+'data'],
                            height=400,
                            key="generated_test_case_display"
                        )
                        
                        # Recreate and save buttons
                        col1, col2 = st.columns(2)
                        with col1:
                            recreate_button = st.button("Recreate", key="new_testcase_recreate")
                            if recreate_button:
                                with st.spinner("Recreating test case, please wait..."):
                                    create_response(session_states[CONST_ACCEPTANCE_CRITERIA_OPTION], 'Create new Test Case', session_states, 1)
                                    analytics = Analytics(default_path, session_states.username)
                                    analytics.write_analytics(CONST_TESTCASE_PAGE, session_states[CONST_ACCEPTANCE_CRITERIA_OPTION], "Recreate")
                        
                        with col2:
                            save_button = st.button("Save", key="new_testcase_save")
                            if save_button:
                                session_states[test_case_save_button_key] = True
                                analytics = Analytics(default_path, session_states.username)
                                analytics.write_analytics(CONST_TESTCASE_PAGE, session_states[CONST_ACCEPTANCE_CRITERIA_OPTION], "Save")
                                with st.spinner("Saving test case..."):
                                    session_states[session_states[CONST_ACCEPTANCE_CRITERIA_OPTION]+'data'] = session_states[session_states[CONST_ACCEPTANCE_CRITERIA_OPTION]+'text']
                                    finalize_data(
                                        page,
                                        session_states[CONST_TESTCASE_FOLDERNAME],
                                        session_states[session_states[CONST_ACCEPTANCE_CRITERIA_OPTION]+'data'],
                                        session_states[CONST_ACCEPTANCE_CRITERIA_OPTION],
                                        session_states
                                    )
                            
                            if session_states[test_case_save_button_key]:
                                feedback_dialog(
                                    session_states,
                                    test_case_save_button_key,
                                    default_path,
                                    session_states.username,
                                    CONST_TESTCASE_PAGE,
                                    session_states[CONST_ACCEPTANCE_CRITERIA_OPTION]
                                )
            else:
                #Selecting UserStory
                session_states[CONST_USER_STORY_TITLE] = st.selectbox("Select a Parent User Story (Created from the User Story Page) or Create new Test Case:", UserStory_titles,index=None,key="Testcase_selectbox")

                if session_states[CONST_USER_STORY_TITLE]!='Create new Test Case' and session_states[CONST_USER_STORY_TITLE]!=None:
                    session_states[CONST_CREATE_NEW_TESTCASE_FLAG]=0
                    prev_title_index=0
                    for i in range(len(UserStory_titles)):
                        if(session_states[CONST_USER_STORY_TITLE]==UserStory_titles[i]):
                            prev_title_index=i
                    folders=split_folders_titles(Acceptance_criteria_titles[prev_title_index],session_states,0)
                    titles=split_folders_titles(Acceptance_criteria_titles[prev_title_index],session_states,1)
                    radio_buttons=titles
            
                    #Selecting a Userstory from the listed radio buttons
                    session_states[CONST_ACCEPTANCE_CRITERIA_OPTION]=st.radio('Select an acceptance criteria :',radio_buttons,on_change=radio_change,args=(radio_buttons,session_states,), index=None)
                    if(session_states[CONST_ACCEPTANCE_CRITERIA_OPTION]):
                        title_index=0
                        #Extracting foldername of the userstory from the list
                        for i in range(len(titles)):
                            if(session_states[CONST_ACCEPTANCE_CRITERIA_OPTION]==titles[i]):
                                title_index=i
                        session_states[CONST_TESTCASE_FOLDERNAME]=folders[title_index]
                        #Creating the response
                        if(session_states[session_states[CONST_ACCEPTANCE_CRITERIA_OPTION]]==0):
                            generate=st.button('Create',key='TestCase_create')
                            if generate:
                                session_states[test_case_save_button_key] = False
                                with st.spinner("Creating "+page+", please wait...."):
                                    session_states[session_states[CONST_ACCEPTANCE_CRITERIA_OPTION]]=1
                                    create_response(session_states[CONST_ACCEPTANCE_CRITERIA_OPTION], session_states[CONST_USER_STORY_TITLE],session_states,0)
                                    analytics = Analytics(default_path, session_states.username)
                                    analytics.write_analytics(CONST_TESTCASE_PAGE, session_states[CONST_ACCEPTANCE_CRITERIA_OPTION], "Parent-Create") 
                                    if session_states[page+"_enable"] == 3:
                                        session_states[page+"_enable"] = 1
                                        session_states[CONST_ACCEPTANCE_CRITERIA_OPTION]=None

                elif(session_states[CONST_USER_STORY_TITLE]=='Create new Test Case' and session_states[CONST_CREATE_NEW_TESTCASE_FLAG]==0):
                    #Userstory_title_str=session_states[CONST_PROMPT_DICTIONARY][CONST_USERSTORY_CREATE_NEW_PROMPT] +"\nContent : "+ session_states['content']
                    #session_states[CONST_USERSTORY_OPTION] = Userstory_title_str

                    # This flag is set to prevent the prompt output from being created multiple times.
                    session_states[CONST_CREATE_NEW_TESTCASE_FLAG]=1
                    with st.spinner("Creating new testcase, please wait...."):
                        session_states[test_case_save_button_key] = False
                        create_response('', session_states[CONST_USER_STORY_TITLE],session_states,0)
                        analytics = Analytics(default_path, session_states.username)
                        analytics.write_analytics(CONST_TESTCASE_PAGE, session_states[CONST_ACCEPTANCE_CRITERIA_OPTION], "Create") 
                    if session_states[page+"_enable"] == 3:
                        session_states[page+"_enable"] = 1
                        session_states[CONST_ACCEPTANCE_CRITERIA_OPTION]=None
                    else:
                        session_states[session_states[CONST_ACCEPTANCE_CRITERIA_OPTION]]=1
                    #For orphan it will create foldername
                    session_states[CONST_TESTCASE_FOLDERNAME]=Next_Orphan_foldername(session_states[CONST_TESTCASE_FINALIZED_PATH],CONST_TESTCASE_PAGE,session_states)
                
                #To recreate and store the response
                if(session_states[CONST_USER_STORY_TITLE]!=None and session_states[CONST_ACCEPTANCE_CRITERIA_OPTION]!=None):
                    #ReCreating and saving the response
                    if(session_states[CONST_ACCEPTANCE_CRITERIA_OPTION]+'data' in session_states):
                        session_states[session_states[CONST_ACCEPTANCE_CRITERIA_OPTION]+'text']=st.text_area(label=session_states[CONST_ACCEPTANCE_CRITERIA_OPTION],label_visibility="collapsed",height=700,value=session_states[session_states[CONST_ACCEPTANCE_CRITERIA_OPTION]+'data'])
                        
                        if(session_states[session_states[CONST_ACCEPTANCE_CRITERIA_OPTION]]<=2):
                            col1, col2 = st.columns(2)
                            with col1:
                                    # generate=st.button('Recreate',key='UserStory_recreate')
                                    st.button('Recreate', key='Userstory_recreate', on_click=recreate_testcase, args=(session_states, page, default_path))
                            
                            #After recreate need to initialize to 1
                            session_states[session_states[CONST_ACCEPTANCE_CRITERIA_OPTION]] = 1
                            save_button=st.button('Save',key='TestCase_save')
                            #Saving the response
                            if save_button:
                                session_states[test_case_save_button_key] = True
                                analytics = Analytics(default_path, session_states.username)
                                analytics.write_analytics(CONST_TESTCASE_PAGE, session_states[CONST_ACCEPTANCE_CRITERIA_OPTION], "Save") 
                                with st.spinner('Saving TestCase....'):
                                    session_states[session_states[CONST_ACCEPTANCE_CRITERIA_OPTION]+'data']=session_states[session_states[CONST_ACCEPTANCE_CRITERIA_OPTION]+'text']
                                    finalize_data(page,session_states[CONST_TESTCASE_FOLDERNAME],session_states[session_states[CONST_ACCEPTANCE_CRITERIA_OPTION]+'data'],session_states[CONST_ACCEPTANCE_CRITERIA_OPTION],session_states)

                            if session_states[test_case_save_button_key]:
                                feedback_dialog(session_states, test_case_save_button_key, default_path, session_states.username, CONST_TESTCASE_PAGE, session_states[CONST_ACCEPTANCE_CRITERIA_OPTION])          
        if verify_log_variable(page, LoggerObject):
            # log_writer(session_states['log_file_descriptor'], page, "load_examples function started")
            logger.info(f"{page} {page} UI page Ended")
        
    except IndexError:
        if UserStory_folder_titles == []:
            st.toast(f'The selected User Story Title "{session_states[CONST_USER_STORY_TITLE]}" is not present in the directory.')
            if verify_log_variable(page, LoggerObject):
                # log_writer(session_states['log_file_descriptor'], page, "load_examples function started")
                logger.error(f"{page} The Selected User Story Title {session_states[CONST_USER_STORY_TITLE]} is not present in the directory.")
    except Exception as e:
        error_msg = handle_exception(e)
        st.toast(error_msg)
        if verify_log_variable(page, LoggerObject):
            # log_writer(session_states['log_file_descriptor'], page, "load_examples function started")
            logger.error(f"{page} {error_msg}")

def write_log(logger_object, page, message):
    if verify_log_variable(page, logger_object):
        logger.info(f"{page} {message}")
# Function to recreate user story from ADO feature
def recreate_user_story_from_ado_feature(session_states, default_path):
    session_states[session_states[CONST_USERSTORY_OPTION]] = 2
    template = session_states[CONST_USERSTORY_USER_TEMPLATE]
    example=session_states[CONST_USERSTORY_USER_EXAMPLE]
    if(template == '' or template == 'None') and (example=='' or example=='None'):
        session_states[session_states[CONST_USERSTORY_OPTION]+'_push_new_US_to_ADO'] = True
    else:
        session_states[session_states[CONST_USERSTORY_OPTION]+'_push_new_US_to_ADO'] = False
    create_response(session_states[CONST_USERSTORY_OPTION], session_states[ADO_US_FEATURE_DETAILS_KEY].get('Title'), session_states, 1)
    analytics = Analytics(default_path, session_states.username)
    analytics.write_analytics(CONST_User_Story, session_states[CONST_USERSTORY_OPTION], "ADO-Parent-Recreate", session_states[CONST_ENTER_ORG_NAME], session_states[CONST_SEL_PROJECT], session_states[CONST_SEL_SITERATION])


def recreate_testcase(session_states, page, default_path):
    session_states[test_case_save_button_key] = False
    with st.spinner("Recreating "+ page +", please wait...."):
        if(session_states[CONST_USER_STORY_TITLE]!='Create new Test Case'):
            create_response(session_states[CONST_ACCEPTANCE_CRITERIA_OPTION],session_states[CONST_USER_STORY_TITLE],session_states,1)
        else:
             if(session_states[CONST_CREATE_NEW_TESTCASE_STATUS] == False):
                create_response(session_states[CONST_ACCEPTANCE_CRITERIA_OPTION],session_states[CONST_USER_STORY_TITLE],session_states,1)
             else:
                st.toast('Error in recreating new TestCase, please create new one before recreating.')
        session_states[session_states[CONST_ACCEPTANCE_CRITERIA_OPTION]]=2

        analytics = Analytics(default_path, session_states.username)
        analytics.write_analytics(CONST_TESTCASE_PAGE, session_states[CONST_ACCEPTANCE_CRITERIA_OPTION], "Recreate")

def recreate_test_case_ado(session_states, page, test_case_id, 
                      organization_name, project, iteration, 
                      default_path):
    """
    Recreates a test case from ADO and prepares it for enhancement.
    
    Parameters:
        session_states (dict): Session state dictionary
        page (str): Current page name
        test_case_id (int): ID of the test case to recreate
        organization_name (str): ADO organization name
        project (str): ADO project name
        iteration (str): ADO iteration path
        default_path (str): Path to default folder
        
    Returns:
        None
    """
    # Log the start of the function
    LoggerObject = session_states[LOGGERCONFIG_OBJECT]
    if verify_log_variable(page, LoggerObject):
        logger.info(f"{page} recreate_test_case_ado function Started")
    
    try:
        # Log analytics for recreating the test case
        analytics = Analytics(default_path, session_states.username)
        analytics.write_analytics(
            CONST_TESTCASE_PAGE, 
            str(test_case_id), 
            "ADO-Recreate", 
            organization_name, 
            project, 
            iteration
        )
        
        # Get the selected test case details
        if test_case_id not in test_case_dict:
            st.toast(f"Test case with ID {test_case_id} not found")
            return
            
        selected_test_case = test_case_dict[test_case_id]
        
        # Format the test case content
        test_case_content = (
            f"Title: {selected_test_case['Title']}\n"
            f"Pre-Conditions: {selected_test_case['PreConditions']}\n"
            f"Steps: {selected_test_case['Steps']}\n"
            f"Expected Results: {selected_test_case['ExpectedResults']}\n"
            f"Additional Information: {selected_test_case['AdditionalInfo']}\n"
        )
        
        # Enhance the test case with recreate flag set to 1
        enhanced_content = enhance_test_case(test_case_content, session_states, 1)
        
        # Store the enhanced content in session state
        enhanced_key = f"enhanced_test_case_{test_case_id}"
        session_states[enhanced_key] = enhanced_content
        
        # Set flag for pushing to ADO
        # If template and example are None, allow pushing to ADO
        template = session_states[CONST_TESTCASE_USER_TEMPLATE]
        example = session_states[CONST_TESTCASE_USER_EXAMPLE]
        
        if (template == '' or template == 'None') and (example == '' or example == 'None'):
            session_states["Push_to_UpdateADO_flag"] = True
        else:
            session_states["Push_to_UpdateADO_flag"] = False
            
        # Log the end of the function
        if verify_log_variable(page, LoggerObject):
            logger.info(f"{page} recreate_test_case_ado function Ended")
            
    except Exception as e:
        error_msg = handle_exception(e)
        st.toast(error_msg)
        if verify_log_variable(page, LoggerObject):
            logger.error(f"{page} {error_msg}")
            
def write_log(logger_object, page, message):
    if verify_log_variable(page, logger_object):
        logger.info(f"{page} {message}")

# Function to return list of user stories for the feature title
def load_saved_userstories(feature_key, session_states):
    default_path = session_states[CONST_DEFAULT_FOLDER]
    saved_file_path = os.path.join(default_path, "UserStories", "ADO", "user_story_titles.json")

    # Check if the file exists
    if not os.path.exists(saved_file_path):
        return []

    # Load the data from the file
    try:
        with open(saved_file_path, "r") as file:
            data = json.load(file)
    except ValueError:
        st.toast("Error while reading saved user story file. Returning an empty list.")
        return []

    # Return the user stories for the given feature title
    return [story["title"] for story in data.get(feature_key, [])]

def recreate_userstory(session_states, page, Feature_title, default_path):
    session_states[test_case_save_button_key] = False
    with st.spinner("Recreating "+page+", please wait...."):
        session_states[session_states[CONST_USERSTORY_OPTION]]=2
        if(Feature_title!='Create new User Story'):
            create_response(session_states[CONST_USERSTORY_OPTION],Feature_title,session_states,1)                  
        else:
            create_response(session_states[CONST_USERSTORY_OPTION],'',session_states,1)

        analytics = Analytics(default_path, session_states.username)
        analytics.write_analytics(CONST_User_Story, session_states[CONST_USERSTORY_OPTION], "Recreate")

def testcase_page(session_states):    
    main_page(session_states)

"""
    Load test cases based on the current session state and configuration.

    This function retrieves test cases from a specified project, team, and iteration. It logs the process 
    if logging is enabled for the current page. The test cases are returned in a dictionary format for easy 
    access and a list of titles for display purposes.

    Parameters:
        session_states (dict): A dictionary containing the current session's state and configuration, including 
                               organization name, selected project, team, iteration, and logger configuration.

    Returns:
        tuple: A dictionary of test cases where each key is the case ID and the value is another dictionary 
               containing the test case's title, steps, expected results, and other details, and a list of 
               titles of the test cases.
"""
def load_test_cases(session_states):
    page_name = 'Test Case'
    loggerConfig_object = session_states[LOGGERCONFIG_OBJECT]
    page = session_states[CURRENT_UI_PAGE]
    
    # Verifying page log flag is enabled or not
    if verify_log_variable(page, loggerConfig_object):
        logger.info(f"{page} load_test_cases function Started")

    try:
        # Retrieve the list of test cases from the specified organization, project, team, and iteration
        # We'll use the same function as user stories but handle the response differently to get test cases
        test_cases_list = get_user_stories(session_states[CONST_ENTER_ORG_NAME], 
                                         session_states[CONST_SEL_PROJECT],
                                         session_states[CONST_SEL_STEAM], 
                                         session_states[CONST_SEL_SITERATION], 
                                         page_name, 
                                         session_states)
        
        # Filter for work items that are test cases (you may need to adjust this based on your ADO setup)
        # This assumes that test cases have a Type field with value "Test Case"
        test_cases_list = [item for item in test_cases_list if item.get('Type', '') == 'Test Case']
        
        # Check if the retrieved test cases are in list format
        if isinstance(test_cases_list, list):
            FT = []    
            test_case_dict = {}
            for test_case in test_cases_list:
                tc_list = str(test_case['ID']) + '~' + test_case['Title']
                FT.append(tc_list)
                test_case_dict[test_case['ID']] = {
                    "Title": test_case['Title'],
                    "Steps": test_case.get('Steps', ''),
                    "ExpectedResults": test_case.get('ExpectedResults', ''),
                    "PreConditions": test_case.get('PreConditions', ''),
                    "AdditionalInfo": test_case.get('AdditionalInfo', '')
                }
            if verify_log_variable(page, loggerConfig_object):
                logger.info(f"{page} load_test_cases function Ended")
            return test_case_dict, FT
        else:
            # Handle the case where the return value is not a list
            return {}, []  # or return an error message depending on your design    
    except KeyError as e:
        st.toast(f"Key error: {e}. Please check the session state keys.")
        if verify_log_variable(page, loggerConfig_object):
            logger.error(f"{page} Key error: {e}. Please check the session state keys.")
        return {}, []  # Return empty structures on error    
    except TypeError as type_err:
        if verify_log_variable(page, loggerConfig_object):
            logger.error(f"{page} Type error occurred: {type_err}")
        st.toast(f"Type error occurred: {type_err}")
        return {}, []    
    except Exception as e:
        if verify_log_variable(page, loggerConfig_object):
            logger.error(f"{page} An error occurred while loading test cases: {e}")
        st.toast(f"An error occurred while loading test cases: {e}")
        return {}, []  # Return empty structures on error

def update_test_case_in_ado(session_states, test_case_id, updated_content):
    """
    Updates a test case in Azure DevOps with the provided content.
    
    Parameters:
        session_states (dict): Dictionary containing session state information
        test_case_id (int): The ID of the test case to update
        updated_content (str): The updated content for the test case
        
    Returns:
        str: Error message if an error occurred, otherwise empty string
    """
    page = session_states[CURRENT_UI_PAGE]
    LoggerObject = session_states[LOGGERCONFIG_OBJECT]
    
    if verify_log_variable(page, LoggerObject):
        logger.info(f"{page} update_test_case_in_ado function Started")
    
    try:
        # Call the update_work_item function to update the test case in ADO
        error_msg = update_work_item(
            session_states[CONST_ENTER_ORG_NAME], 
            session_states[CONST_SEL_PROJECT], 
            test_case_id, 
            updated_content,
            session_states
        )
        
        if error_msg:
            if verify_log_variable(page, LoggerObject):
                logger.error(f"{page} Error updating test case in ADO: {error_msg}")
            return error_msg
            
        if verify_log_variable(page, LoggerObject):
            logger.info(f"{page} update_test_case_in_ado function Ended")
        return ""
    except Exception as e:
        error_msg = handle_exception(e)
        if verify_log_variable(page, LoggerObject):
            logger.error(f"{page} {error_msg}")
        return error_msg

def enhance_test_case(test_case_content, session_states, recreate_flag=0):
    """
    Enhances a test case by using AI to improve its content.
    
    Parameters:
        test_case_content (str): The original test case content
        session_states (dict): Dictionary containing session state information
        recreate_flag (int): Flag indicating whether to recreate the test case
        
    Returns:
        str: The enhanced test case content
    """
    page = session_states[CURRENT_UI_PAGE]
    LoggerObject = session_states[LOGGERCONFIG_OBJECT]
    
    if verify_log_variable(page, LoggerObject):
        logger.info(f"{page} enhance_test_case function Started")
    
    try:
        temperature = session_states[CONST_TEMPERATURE]
        prompt = session_states[CONST_TESTCASE_USER_TEXT]
        template = session_states[CONST_TESTCASE_USER_TEMPLATE]
        example = session_states[CONST_TESTCASE_USER_EXAMPLE]
        
        if template == '' or template == 'None':
            template = session_states[CONST_PROMPT_DICTIONARY][CONST_TESTCASE_DEFAULT_TEMPLATE]
        
        # Define a custom prompt for enhancing existing test cases
        enhance_prompt = session_states[CONST_PROMPT_DICTIONARY].get(
            'CONST_TESTCASE_ENHANCE_PROMPT',
            "Enhance this test case by improving its clarity, coverage, and following best practices: "
        )
        
        # Combine the enhance prompt with the original test case content
        combined_content = f"{enhance_prompt}\n\n{test_case_content}"
        
        # Call TestCaseDataRet to enhance the test case
        response = TestCaseDataRet(
            prompt, 
            template, 
            example,
            session_states[CONST_DEFAULT_FOLDER], 
            '', 
            combined_content,
            session_states[CONST_CONTENT],
            session_states[CONST_PROMPT_DICTIONARY][CONST_TESTCASE_DEFAULT_PROMPT], 
            session_states, 
            recreate_flag, 
            temperature
        )
        
        if verify_log_variable(page, LoggerObject):
            logger.info(f"{page} enhance_test_case function Ended")
        
        # Return the enhanced test case content (first element of response)
        return response[0]
    except Exception as e:
        error_msg = handle_exception(e)
        st.toast(error_msg)
        if verify_log_variable(page, LoggerObject):
            logger.error(f"{page} {error_msg}")
        return test_case_content  # Return original content on error

def enhance_and_push_test_case(session_states):
    """
    Enhances an existing test case and pushes it back to ADO.
    
    Parameters:
        session_states (dict): Dictionary containing session state information
        
    Returns:
        bool: True if successful, False otherwise
    """
    page = session_states[CURRENT_UI_PAGE]
    LoggerObject = session_states[LOGGERCONFIG_OBJECT]
    
    if verify_log_variable(page, LoggerObject):
        logger.info(f"{page} enhance_and_push_test_case function Started")
    
    try:
        # Get the selected test case ID
        if 'selected_test_case_id' not in session_states or not session_states['selected_test_case_id']:
            st.toast("No test case selected")
            return False
        
        test_case_id = session_states['selected_test_case_id']
        
        # Get the original test case content
        if test_case_id not in test_case_dict:
            st.toast(f"Test case with ID {test_case_id} not found")
            return False
        
        test_case = test_case_dict[test_case_id]
        
        # Format the test case content
        test_case_content = (
            f"Title: {test_case['Title']}\n"
            f"Pre-Conditions: {test_case['PreConditions']}\n"
            f"Steps: {test_case['Steps']}\n"
            f"Expected Results: {test_case['ExpectedResults']}\n"
            f"Additional Information: {test_case['AdditionalInfo']}\n"
        )
        
        # Enhance the test case
        enhanced_content = enhance_test_case(test_case_content, session_states, 1)
        
        # Store the enhanced content in session state
        session_states[f"enhanced_test_case_{test_case_id}"] = enhanced_content
        
        # Update test case in ADO
        error_msg = update_test_case_in_ado(session_states, test_case_id, enhanced_content)
        
        if error_msg:
            st.toast(f"Error updating test case in ADO: {error_msg}")
            return False
        
        # Log the successful enhancement and push
        analytics = Analytics(session_states[CONST_DEFAULT_FOLDER], session_states.username)
        analytics.write_analytics(
            CONST_TESTCASE_PAGE, 
            str(test_case_id), 
            "ADO-Enhance-Push", 
            session_states[CONST_ENTER_ORG_NAME], 
            session_states[CONST_SEL_PROJECT], 
            session_states[CONST_SEL_SITERATION]
        )
        
        if verify_log_variable(page, LoggerObject):
            logger.info(f"{page} enhance_and_push_test_case function Ended")
        
        return True
    except Exception as e:
        error_msg = handle_exception(e)
        st.toast(error_msg)
        if verify_log_variable(page, LoggerObject):
            logger.error(f"{page} {error_msg}")
        return False
