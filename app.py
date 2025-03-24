import os
import streamlit as st
import pandas as pd
import openai
import matplotlib.pyplot as plt

# Load the OpenAI API key
openai.api_key = os.environ.get("OPENAI_API_KEY", "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")
st.set_page_config(page_title="AI CSV Analyzer", layout="wide")
st.title("AI-Powered CSV/XLS Analyzer")

if "prompt_history" not in st.session_state:
    st.session_state.prompt_history = []
if "feedback" not in st.session_state:
    st.session_state.feedback = {}

uploaded_files = st.file_uploader("Upload CSV or Excel files", type=["csv", "xls", "xlsx"], accept_multiple_files=True)

if uploaded_files:
    file_names = [f.name for f in uploaded_files]
    selected_file = st.selectbox("Select a file", file_names)
    selected_data = next((f for f in uploaded_files if f.name == selected_file), None)

    if selected_data:
        try:
            # Load file (CSV or Excel)
            if selected_file.endswith(".csv"):
                df = pd.read_csv(selected_data)
            else:
                df = pd.read_excel(selected_data)

            if len(df) < 250:
                st.error(f"The dataset must have at least 250 rows. Your dataset has only {len(df)} rows.")
            else:
                # Data preview section
                num_rows = st.number_input("Show top N rows", min_value=1, max_value=len(df), value=5)
                st.dataframe(df.head(num_rows))
                
                # Graph Generation Section
                st.subheader("Generate Graph")
                graph_type = st.selectbox("Graph Type", ["Line", "Bar", "Scatter", "Histogram"])
                columns = st.multiselect("Select Columns", df.columns.tolist())
                if st.button("Generate Graph"):
                    if not columns:
                        st.error("Select at least one column.")
                    else:
                        fig, ax = plt.subplots()
                        if graph_type == "Line":
                            df[columns].plot(ax=ax)
                        elif graph_type == "Bar":
                            df[columns].plot(kind="bar", ax=ax)
                        elif graph_type == "Scatter":
                            if len(columns) < 2:
                                st.error("Scatter plot requires two columns.")
                            else:
                                df.plot(kind="scatter", x=columns[0], y=columns[1], ax=ax)
                        elif graph_type == "Histogram":
                            df[columns].plot(kind="hist", ax=ax, bins=20)
                        st.pyplot(fig)
                
                # AI Section
                st.subheader("Ask a question about the data")
                # Allow reusing previous questions.
                if st.session_state.prompt_history:
                    reused_prompt = st.selectbox("Reuse previous question", [""] + st.session_state.prompt_history[::-1])
                    if reused_prompt:
                        question = reused_prompt
                    else:
                        question = st.text_input("Your question")
                else:
                    question = st.text_input("Your question")
                
                if question:
                    with st.spinner("Processing..."):
                        # Dynamic CSV Sampling Based on Token Limit
                        def estimate_tokens(text):
                            return len(text) / 4
                        
                        # Set a maximum allowed token count for the CSV sample.
                        max_allowed_tokens_for_csv = 3000
                        
                        csv_header = ",".join(df.columns) + "\n"
                        csv_sample = csv_header

                        for _, row in df.iterrows():
                            row_str = ",".join(map(str, row.values)) + "\n"
                            if estimate_tokens(csv_sample + row_str) > max_allowed_tokens_for_csv:
                                break
                            csv_sample += row_str
                        
                        #warning if the dataset is large.
                        if len(df) > 100:
                            st.warning("Large dataset: only a sample (up to 3000 tokens) is used for AI analysis.")
                        
                        prompt_text = (
                            f"You are a data analyst. Here is a sample of the dataset:\n\n"
                            f"{csv_sample}\n\n"
                            f"Answer this question:\n{question}"
                        )
                        
                        try:
                            response = openai.ChatCompletion.create(
                                model="gpt-3.5-turbo",
                                messages=[
                                    {"role": "system", "content": "You are a helpful data assistant."},
                                    {"role": "user", "content": prompt_text}
                                ],
                                temperature=0.5,
                                max_tokens=500
                            )
                            answer = response["choices"][0]["message"]["content"]
                            st.success("Answer:")
                            st.write(answer)
                        except Exception as ai_err:
                            st.error(f"Error generating AI response: {ai_err}")
                        
                        # Save prompt history
                        if question not in st.session_state.prompt_history:
                            st.session_state.prompt_history.append(question)
                        
                        # Feedback
                        st.markdown("### Was this answer helpful?")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("👍 Yes"):
                                st.session_state.feedback[question] = "👍"
                                st.success("Thanks for your feedback!")
                        with col2:
                            if st.button("👎 No"):
                                st.session_state.feedback[question] = "👎"
                                st.info("We'll work on improving!")
                        if question in st.session_state.feedback:
                            st.caption(f"Feedback: {st.session_state.feedback[question]}")
        except Exception as e:
            st.error(f"Error reading file: {e}")
else:
    st.info("Upload a file to get started.")

