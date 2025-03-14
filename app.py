import os
import streamlit as st
from langgraph.graph import StateGraph
from typing import TypedDict, List, Dict, Any
from langchain_groq import ChatGroq
from langchain.prompts.chat import ChatPromptTemplate
from dotenv import load_dotenv


# API Keys

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not set in the environment variables.")


# Prompts Templates

AMAZON_SEARCH_PROMPT = """
You are a smart shopping assistant. Search for the best deals on Amazon for {product} in the {section} category.
Provide results in a structured format:
- Title
- Price
- Ratings
- URL
"""

PRODUCT_RECOMMENDATION_PROMPT = """
Given the search results from Amazon, analyze the best product based on price, ratings, and availability.
Provide a recommendation in this format: 

Search Results: {amazon_results}

**Recommendation:**
[Product Name]
- Price: $X.XX
- Rating: X.X stars
- Buy from: [Retailer Name]
- Reason: (Short justification)
"""


# Global LLM Object (LLM model could be changed) 
llm = ChatGroq(api_key=GROQ_API_KEY, model="mixtral-8x7b-32768", temperature=0.5)


# Define Agent State
class AgentState(TypedDict):
    product: str
    product_type: str
    search_results: List[Dict[str, Any]]
    recommendation: str

# Function to search Amazon
def search_amazon_node(state: AgentState):
    """Uses Groq API (Mixtral-8x7b) to search Amazon for the product."""
    prompt = ChatPromptTemplate.from_template(AMAZON_SEARCH_PROMPT)

    query = prompt.format(product=state["product"], section=state["product_type"])  
    response = llm.invoke(query)

    results = []
    product = {}

    for line in response.content.split("\n"):
        if "Title:" in line:
            product = {"title": line.replace("Title:", "").strip()}
        elif "Price:" in line:
            product["price"] = line.replace("Price:", "").strip()
        elif "Ratings:" in line:
            product["ratings"] = line.replace("Ratings:", "").strip()
        elif "URL:" in line:
           
            search_query = product["title"].replace(" ", "+")
            product["url"] = f"https://www.amazon.com/s?k={search_query}"  

            results.append(product)  # Save only when all fields are filled

    state["search_results"] = results if results else [{"title": "No products found"}]
    return state

def provide_recommendation_node(state: AgentState):
    """Uses Groq API to provide a structured product recommendation."""
    prompt = ChatPromptTemplate.from_template(PRODUCT_RECOMMENDATION_PROMPT)

    query = prompt.format(amazon_results=str(state["search_results"]))  # 
    response = llm.invoke(query)

    state["recommendation"] = response.content if response.content else "No recommendation available."
    return state


builder = StateGraph(AgentState)
builder.add_node("start", search_amazon_node)
builder.add_node("product_recommendation", provide_recommendation_node)

builder.set_entry_point("start")
builder.add_edge("start", "product_recommendation")

# Compile the graph
graph = builder.compile()

# Main Streamlit App
def main():
    st.image("https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg", width=200)
    st.title("Amazon Product Recommendation AI 🔍")
    st.write("This AI searches for the best deals on Amazon and recommends the best product.")
    st.markdown("1. **Enter Product Name:** Type the product you wish to search for in the text input field.")
    st.markdown("2. **Select Product Type:** Choose the relevant product category from the dropdown list.")
    st.markdown("3. **Perform Search:** Click the 'Search' button to initiate the product search.")
    st.markdown("4. **Review Results:** Browse through the search results displayed below the steps.")
    st.write("Developed by [*Alvajoy Asante*](https://www.linkedin.com/in/alvajoy-asante)")



    col1, col2 = st.columns(2)
    with col1:
        product_name = st.text_input("Enter the product name:")
    with col2:
        product_types = [
            "Computers", "Smartphones", "Tablets", "TVs", "Cameras", "Audio Equipment",
            "Home Appliances", "Books", "Clothing", "Sports Equipment", "Toys & Games",
            "Health & Beauty", "Automotive", "Garden & Outdoor", "Office Supplies"
        ]
        selected_product_type = st.selectbox("Select Product Type", sorted(product_types))

    if st.button("Search"):
        if product_name:
            with st.spinner(f"Searching for {product_name}..."):
                results = graph.invoke({"product": product_name, "product_type": selected_product_type})

                if results and results.get("search_results"):
                    st.subheader("🔍 Search Results")
                    for idx, item in enumerate(results["search_results"]):
                        st.write(f"**{idx+1}. {item.get('title', 'No Title')}**")
                        st.write(f"- 💲 Price: {item.get('price', 'N/A')}")
                        st.write(f"- ⭐ Rating: {item.get('ratings', 'N/A')}")
                        st.write(f"- 🔗 [View Product]({item.get('url', '#')})")
                        st.write("---")

                    st.subheader("✅ Best Recommendation")
                    st.write(results["recommendation"])

                else:
                    st.warning("No results found. Try a different search.")
        else:
            st.warning("Please enter a product name.")

if __name__ == "__main__":
    main()