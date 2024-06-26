import time
from pathlib import Path
from fastapi import FastAPI
from just_agents.llm_session import LLMSession, LLMOptions
from literature.routes import hybrid_search
from gpt.routes import longevity_gpt
from genetics.main import rsid_lookup, gene_lookup, pathway_lookup, disease_lookup, sequencing_info
from starlette.responses import StreamingResponse
from dotenv import load_dotenv
import os
load_dotenv(override=True)
# What is the influence of different alleles in rs10937739 and what is MTOR gene?
app = FastAPI(title="Genetics Genie API endpoint.")


@app.get("/", description="Defalt message", response_model=str)
async def default():
    return "This is default page for Genetics Genie API endpoint."


@app.post("/v1/chat/completions")
async def chat_completions(request: dict):
    print(request)
    if request["model"].startswith("openrouter"):
        api_base = "https://openrouter.ai/api/v1"
        api_key = os.getenv('OPEN_ROUTER_KEY')
    else:
        api_base = None
        api_key = None

    curent_llm:LLMOptions = LLMOptions(request["model"], api_base=api_base, temperature=float(request["temperature"]), api_key=api_key)  #LLMOptions(model=request["model"], temperature=request["temperature"])

    session: LLMSession = LLMSession(
        llm_options=curent_llm,
        tools=[hybrid_search, longevity_gpt, rsid_lookup, gene_lookup, pathway_lookup, disease_lookup, sequencing_info]
    )
    with open(Path(Path(__file__).parent, "data", "system_prompt.txt")) as sys_prompt:
        session.instruct(sys_prompt.read())
    try:
        if request["messages"]:
            if bool(request.get("stream")) == True:
                return StreamingResponse(
                    session.stream_all(request["messages"], run_callbacks=False), media_type="application/x-ndjson"
                )

            resp_content = session.query_all(request["messages"], run_callbacks=False)
        else:
            resp_content = "Something goes wrong, request did not contain messages!!!"
    except Exception as e:
        resp_content = str(e)

    return {
        "id": "1",
        "object": "chat.completion",
        "created": time.time(),
        "model": curent_llm["model"],
        "choices": [{"message": {"role":"assistant", "content":resp_content}}],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8088)