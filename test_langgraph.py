from src.graph.workflow import app

if __name__ == "__main__":

    result = app.invoke({
        "job_description": "AI Engineer with Python, ML, LangChain",
        "resumes": [
            "Python developer with ML experience",
            "Java developer with Spring Boot"
        ]
    })

    print("\nFINAL OUTPUT:\n")
    print(result)