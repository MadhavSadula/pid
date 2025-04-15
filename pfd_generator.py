import streamlit as st
from pyflowsheet import Flowsheet, UnitOperation, Distillation, Vessel, BlackBox, Pump, Stream, StreamFlag, Valve, HeatExchanger, Mixer, Splitter, Port, SvgContext
from pyflowsheet.internals import Tubes, RandomPacking
from pyflowsheet import VerticalLabelAlignment, HorizontalLabelAlignment
import os
import tempfile
import sys

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from genai import CreateChatbot

# Set up the page
st.set_page_config(page_title="Process Flow Diagram Generator", layout="wide")
st.title("AI-Powered Process Flow Diagram Generator")

# Initialize session state for chat memory
if "chat_memory" not in st.session_state:
    st.session_state.chat_memory = []

# Sidebar for settings
with st.sidebar:
    st.header("Settings")
    st.markdown("### How to use:")
    st.markdown("1. Describe your process in the text area")
    st.markdown("2. Click 'Generate PFD'")
    st.markdown("3. The AI will generate a process flow diagram")

# Main content area
st.write("""
Describe your process in natural language. For example:
- "A distillation column with a feed stream, condenser at the top, and reboiler at the bottom"
- "A heat exchanger followed by a reactor and a separator"
- "A mixing tank with two input streams and one output stream"
""")

# Text input for process description
process_description = st.text_area("Describe your process:", height=150)

# Generate button
if st.button("Generate PFD"):
    if not process_description:
        st.error("Please describe your process")
    else:
        try:
            # Create a prompt for the AI
            prompt = f"""
            Based on the following process description, generate Python code using pyflowsheet to create a process flow diagram:
            
            Description: {process_description}
            
            The code should:
            1. Create a Flowsheet object
            2. Define all necessary unit operations
            3. Connect the units with streams
            4. Position the units appropriately
            5. Save the diagram as an SVG file
            
            Return only the Python code, no explanations.
            """
            
            # Get AI response using the CreateChatbot function
            result = CreateChatbot(prompt, st.session_state)
            
            if isinstance(result, list) and result[0] == 0:
                generated_code = result[1]
                
                # Create a temporary directory for the SVG file
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Execute the generated code
                    exec(generated_code)
                    
                    # Display the generated SVG
                    svg_path = os.path.join(temp_dir, "generated_pfd.svg")
                    with open(svg_path, "rb") as f:
                        svg_data = f.read()
                    
                    st.image(svg_data, use_column_width=True)
                    
                    # Show the generated code
                    st.code(generated_code, language="python")
            else:
                st.error(f"Error generating diagram: {str(result)}")
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

# Footer
st.markdown("---")
st.markdown("""
This application uses:
- Azure OpenAI GPT-4 for process understanding and code generation
- pyflowsheet for diagram generation
- Streamlit for the web interface
""") 