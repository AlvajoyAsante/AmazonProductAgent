import os
from langchain_community.tools import TavilySearchResults
from tavily import TavilyClient
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List, Dict, Any
from langchain_core.runnables.graph import MermaidDrawMethod
import streamlit as st
from IPython.display import display, Image
import re
from langchain_groq import ChatGroq
from langchain.prompts.chat import ChatPromptTemplate

os.environ["TAVILY_API_KEY"] = os.getenv('TAVILY_API_KEY')
os.environ["GROQ_API_KEY"] = os.getenv('GROQ_API_KEY')

AMAZON_SEARCH_PROMPT = "Search for the best deals on Amazon for {product} in the {section} category."

BEST_DEAL_PROMPT = "Given the following search results from Amazon, find the best deal for the product. Amazon Results: {amazon_results} | Best Deal:"

AMAZON_PRODUCT_BY_LINKS_PROMPT = "Using the provided Amazon links, retrieve detailed information about the product including price, availability, and ratings: {amazon_links}"

PRODUCT_RECOMMENDATION_PROMPT = """Based on the search results, product details, and reviews, recommend the best product to purchase and specify the retailer. Here are a few examples to guide your response: 
    Example 1: 
    Input:
    - Amazon Results: ["Product X", "Price: $25", "Rating: 4.5"]
    - eBay Results: ["Product X", "Price: $23", "Rating: 4.3"]
    
    Output:
    Recommendation: Choose Product X from eBay due to the lower price while maintaining similar quality.
    Example 2:
    Input:
    - Amazon Results: ["Product Y", "Price: $45", "Rating: 4.7"]
    - eBay Results: ["Product Y", "Price: $48", "Rating: 4.7"]
    Output:
    Recommendation: Choose Product Y from Amazon as it offers a better deal for the same quality.
    Now, please provide a detailed recommendation for the queried product using similar reasoning """

class AgentState(TypedDict):
    product: str
    product_type: str
    search_result: List[Dict[str, Any]]
    reviews: List[str]
    processed_reviews: str
    recommendation: str

def search_amazon_node(state: AgentState):
    # Were using the TavilySearchResults tool to search for products on Amazon and eBay
    tool = TavilySearchResults(
        max_results=3,
        search_depth="advanced",
        include_answer=True,
        include_raw_content=True,
        include_images=True,
        include_domains=["http://www.amazon.com"],
        # exclude_domains=[...],
        # name="...",            # overwrite default tool name
        # description="...",     # overwrite default tool description
        # args_schema=...,       # overwrite default args_schema: BaseModel
    )
    search_results = tool.invoke({
        "query": AMAZON_SEARCH_PROMPT.format(product=state["product"], section=state["product_type"])
    })
    state["search_result"] = search_results
    return state

def grab_product_reviews_node(state: AgentState):
    pass

def provide_recommendation_node(state: AgentState):
    pass

# Building the state graph
builder = StateGraph(AgentState)

# Add nodes to the graph 
builder.add_node("start", search_amazon_node)
builder.add_node("grab_product_review", grab_product_reviews_node)
builder.add_node("product_recommendation", provide_recommendation_node)

builder.set_entry_point("start")

# Add edges to the graph
builder.add_edge("start", "grab_product_review")
builder.add_edge("grab_product_review", "product_recommendation")

# Compile 
graph = builder.compile()


# Main
def main():
    amazon_logo_url = "https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg"
    st.image(amazon_logo_url, width=200)
    st.title("Amazon Product Recommendation Agent 🔍")
    st.write("This agent searches for products on Amazon based on the detailed information provided below. ")
    # st.markdown("### Steps to Use the Model:")s
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
            "Computers",
            "Smartphones",
            "Tablets",
            "TVs",
            "Cameras",
            "Audio Equipment",
            "Home Appliances",
            "Books",
            "Clothing",
            "Sports Equipment",
            "Toys & Games",
            "Health & Beauty",
            "Automotive",
            "Garden & Outdoor",
            "Office Supplies"
        ]
        selected_product_type = st.selectbox("Select Product Type", sorted(product_types))

    if st.button("Search"):
        if product_name:
            with st.spinner(f"Searching for the best deals on Amazon for {product_name}"):

                results = graph.stream({"product": product_name, "product_type": selected_product_type})
                print(list(results))
                
                if results:
                    print("Results found")
                    st.subheader("Search Results:")
                else:
                    st.write("No results found.")
        else:
            st.write("Please enter a product name.")

if __name__ == "__main__":
    main()