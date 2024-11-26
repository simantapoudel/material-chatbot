from langchain.prompts import PromptTemplate
from langchain_community.llms import Ollama
import re
from processing import vector_store

llm = Ollama(model="llama3.2:1b", base_url="https://llm.bicbioeng.org")

#Prompt template to include conversation history
prompt = PromptTemplate(
    input_variables=["question", "context", "chat_history"],
    template="""
    You are an AI chatbot with expertise in Materials data.
    Your task is to answer the user's question using the provided context as a reference.
    If the context does not provide enough information to answer the question,
    you should indicate that. If any part of your answer is uncertain or could
    be inaccurate, acknowledge that and provide the best possible response based
    on the available knowledge.

    The user might sometimes just give you a material id or formula, based on
    the context provided try to generate a response best suited neatly.

    Previous conversation:
    {chat_history}

    Context: {context}

    Question: {question}

    Answer:
    """
)

prompt_decomposition = PromptTemplate(
    input_variables=["question", "format"],
    template="""
    I have a database of materials data, and based on the question of the user, you will retreive data from materials database.
    Sometimes the user might query with just the material id which looks like mp-100000.
    So i will try to retrieve the data of the material, determine how many data i should retrieve
    as k=5 will retrieve 5 data for example.

    In response just give me the new question and the number of data i need to retrieve.
    I expect nothing else than the question and the number of data.

    please give the answer in the below format:
    {format}

    Question: {question}

    Answer:
    """
)

format = "['question': 'mp-100000', 'k': 1]"

chain = prompt | llm
chain_decomposition = prompt_decomposition | llm

def format_chat_history(history):
    """Convert chat history into a formatted string."""
    formatted_history = []
    for speaker, message in history:
        formatted_history.append(f"{speaker}: {message}")
    return "\n".join(formatted_history)

def ask_question(query, history):
    chat_history = format_chat_history(history)

    new_question = chain_decomposition.invoke({"question": query, "format": format})
    match = re.search(r"\['question': '([^']*)', 'k': (\d+)]", new_question)

    if match:
        extracted_question = match.group(1)
        extracted_k = int(match.group(2))
        print(f"Extracted Question: {extracted_question}")
        print(f"Extracted k: {extracted_k}")
    else:
        print("Response format is incorrect.")
        extracted_question = query
        extracted_k = 5

    k = extracted_k or 2

    filter_criteria = None
    if re.match(r"mp-\d+", extracted_question):
        filter_criteria = [{"term": {"metadata.material_id.keyword": extracted_question}}]

    if filter_criteria:
        results = vector_store.similarity_search_with_score(
            query=extracted_question,
            k=k,
            filter=filter_criteria
        )
    else:
        results = vector_store.similarity_search_with_score(query=extracted_question, k=k)

    context = "\n".join(doc.page_content for doc, _ in results)

    print("Final Context Passed to Prompt:", context)

    response = chain.invoke({
        "question": query,
        "context": context,
        "chat_history": chat_history
    })

    return response