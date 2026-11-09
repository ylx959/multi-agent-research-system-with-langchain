from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.tools.tools import web_search, scrape_url
from dotenv import load_dotenv

load_dotenv()

#create_agent(modern) vs. create_react_agent(older)

# Model Initialization
llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite")


#start to build different agent !

# 1st Agent : Search Agent
def build_search_agent():
    return create_agent(
        model= llm,
        tools=[web_search],
        system_prompt=(
            "You are a web research agent. Always call the web_search tool before answering; "
            "never answer from memory. Base your summary only on the search results and "
            "mention the URL of each source you use."
        ),
    )

# 2nd Agent : Reader Agent
def build_reader_agent():
    return create_agent(
        model= llm,
        tools=[scrape_url],
        system_prompt=(
            "You are a reading agent. Always call the scrape_url tool on the most relevant URL. "
            "If scraping fails (an error, a block or a timeout), try the next most relevant URL, "
            "up to 3 attempts. Summarise only what the scraped pages actually say."
        ),
    )


#writer chain 

#system prompt and human prompt

writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Write clear, structured and insightful reports."),
    ("human", """Write a detailed research report on the topic below.

Topic: {topic}

Sources (the ONLY sources you may cite):
{sources}

Research Gathered:
{research}

Structure the report as:
- Introduction
- Key Findings (minimum 3 well-explained points). End every finding with a line that starts
  with "Sources:" followed by one or more markdown links in the form [Source title](URL).
  Use only URLs from the Sources list above, copied exactly. Never invent or change a URL.
- Conclusion

Do not write a separate Sources section at the end; it is added automatically.
Be detailed, factual and professional."""),
])

writer_chain = writer_prompt | llm | StrOutputParser()




#critic_chain 

critic_prompt = ChatPromptTemplate.from_messages([
     ("system", "You are a sharp and constructive research critic. Be honest and specific."),
    ("human", """Review the research report below and evaluate it strictly.

Report:
{report}

Respond in this exact format:

Score: X/10

Strengths:
- ...
- ...

Areas to Improve:
- ...
- ...

One line verdict:
..."""),
])

critic_chain = critic_prompt | llm | StrOutputParser()

