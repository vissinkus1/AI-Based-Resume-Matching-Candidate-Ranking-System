"""
Script to expand the skills taxonomy to 310+ skills.
"""
import json
from pathlib import Path

TAX_PATH = Path(__file__).resolve().parent.parent / "app" / "data" / "skills_taxonomy.json"

new_skills = [
    # programming_languages
    {"canonical": "Julia", "category": "programming_languages", "aliases": ["julia lang"]},
    {"canonical": "Solidity", "category": "programming_languages", "aliases": ["solidity lang", "smart contracts"]},
    {"canonical": "Fortran", "category": "programming_languages", "aliases": ["fortran 90", "fortran 95"]},
    {"canonical": "Erlang", "category": "programming_languages", "aliases": ["erlang otp"]},
    {"canonical": "Clojure", "category": "programming_languages", "aliases": ["clojurescript", "clojure lang"]},
    {"canonical": "Zig", "category": "programming_languages", "aliases": ["zig lang"]},
    {"canonical": "Visual Basic", "category": "programming_languages", "aliases": ["vb.net", "vba", "visual basic .net"]},
    {"canonical": "Delphi", "category": "programming_languages", "aliases": ["object pascal", "delphi pascal"]},

    # frontend
    {"canonical": "SolidJS", "category": "frontend", "aliases": ["solid.js", "solid js"]},
    {"canonical": "Astro", "category": "frontend", "aliases": ["astro.build", "astro framework"]},
    {"canonical": "Alpine.js", "category": "frontend", "aliases": ["alpinejs", "alpine js"]},
    {"canonical": "Chakra UI", "category": "frontend", "aliases": ["chakra-ui"]},
    {"canonical": "Ant Design", "category": "frontend", "aliases": ["antd", "ant-design"]},
    {"canonical": "Semantic UI", "category": "frontend", "aliases": ["semantic-ui"]},
    {"canonical": "Bulma", "category": "frontend", "aliases": ["bulma css"]},
    {"canonical": "RxJS", "category": "frontend", "aliases": ["reactive extensions", "rxjs library"]},
    {"canonical": "MobX", "category": "frontend", "aliases": ["mobx state tree"]},
    {"canonical": "Zustand", "category": "frontend", "aliases": ["zustand state"]},
    {"canonical": "Web Components", "category": "frontend", "aliases": ["custom elements", "shadow dom"]},
    {"canonical": "Three.js", "category": "frontend", "aliases": ["threejs", "three js", "webgl 3d"]},

    # backend
    {"canonical": "Quarkus", "category": "backend", "aliases": ["quarkus io", "quarkus framework"]},
    {"canonical": "Micronaut", "category": "backend", "aliases": ["micronaut framework"]},
    {"canonical": "Gin", "category": "backend", "aliases": ["gin-gonic", "gin web framework"]},
    {"canonical": "Fiber", "category": "backend", "aliases": ["go fiber", "gofiber"]},
    {"canonical": "Actix", "category": "backend", "aliases": ["actix-web", "actix web"]},
    {"canonical": "Axum", "category": "backend", "aliases": ["axum framework"]},
    {"canonical": "Phoenix", "category": "backend", "aliases": ["phoenix framework", "elixir phoenix"]},
    {"canonical": "Vert.x", "category": "backend", "aliases": ["vertx", "eclipse vert.x"]},
    {"canonical": "Sanic", "category": "backend", "aliases": ["sanic framework"]},
    {"canonical": "Tornado", "category": "backend", "aliases": ["tornado web"]},
    {"canonical": "Pyramid", "category": "backend", "aliases": ["pyramid framework"]},
    {"canonical": "Ktor", "category": "backend", "aliases": ["ktor framework"]},
    {"canonical": "Symfony", "category": "backend", "aliases": ["symfony framework", "symfony php"]},
    {"canonical": "CodeIgniter", "category": "backend", "aliases": ["codeigniter framework"]},
    {"canonical": "Sinatra", "category": "backend", "aliases": ["sinatra rb"]},
    {"canonical": "Dropwizard", "category": "backend", "aliases": ["dropwizard framework"]},

    # databases
    {"canonical": "ClickHouse", "category": "databases", "aliases": ["clickhouse db"]},
    {"canonical": "DuckDB", "category": "databases", "aliases": ["duck db"]},
    {"canonical": "CockroachDB", "category": "databases", "aliases": ["cockroach db", "cockroach"]},
    {"canonical": "ScyllaDB", "category": "databases", "aliases": ["scylla db", "scylladb"]},
    {"canonical": "TimescaleDB", "category": "databases", "aliases": ["timescale db", "timescaledb"]},
    {"canonical": "InfluxDB", "category": "databases", "aliases": ["influx db", "influxdb"]},
    {"canonical": "Apache HBase", "category": "databases", "aliases": ["hbase", "hadoop hbase"]},
    {"canonical": "Couchbase", "category": "databases", "aliases": ["couchbase server"]},
    {"canonical": "Pinecone", "category": "databases", "aliases": ["pinecone vector db", "pinecone db"]},
    {"canonical": "ChromaDB", "category": "databases", "aliases": ["chroma db", "chromadb"]},
    {"canonical": "Weaviate", "category": "databases", "aliases": ["weaviate vector db"]},
    {"canonical": "Qdrant", "category": "databases", "aliases": ["qdrant vector db"]},
    {"canonical": "Milvus", "category": "databases", "aliases": ["milvus vector db"]},
    {"canonical": "Supabase", "category": "databases", "aliases": ["supabase db", "supabase platform"]},

    # cloud_devops
    {"canonical": "OpenStack", "category": "cloud_devops", "aliases": ["openstack cloud"]},
    {"canonical": "Podman", "category": "cloud_devops", "aliases": ["podman containers"]},
    {"canonical": "HashiCorp Vault", "category": "cloud_devops", "aliases": ["vault", "hashicorp vault"]},
    {"canonical": "HashiCorp Consul", "category": "cloud_devops", "aliases": ["consul", "hashicorp consul"]},
    {"canonical": "Nomad", "category": "cloud_devops", "aliases": ["hashicorp nomad"]},
    {"canonical": "Pulumi", "category": "cloud_devops", "aliases": ["pulumi iac"]},
    {"canonical": "AWS CloudFormation", "category": "cloud_devops", "aliases": ["cloudformation", "cfn"]},
    {"canonical": "Datadog", "category": "cloud_devops", "aliases": ["datadog monitoring", "datadog apm"]},
    {"canonical": "New Relic", "category": "cloud_devops", "aliases": ["newrelic", "new relic apm"]},
    {"canonical": "Splunk", "category": "cloud_devops", "aliases": ["splunk enterprise", "splunk logging"]},
    {"canonical": "ArgoCD", "category": "cloud_devops", "aliases": ["argo cd", "argocd"]},
    {"canonical": "Istio", "category": "cloud_devops", "aliases": ["istio service mesh"]},
    {"canonical": "Traefik", "category": "cloud_devops", "aliases": ["traefik proxy"]},
    {"canonical": "OpenShift", "category": "cloud_devops", "aliases": ["red hat openshift", "openshift container platform"]},

    # ai_ml
    {"canonical": "XGBoost", "category": "ai_ml", "aliases": ["xgboost algorithm"]},
    {"canonical": "LightGBM", "category": "ai_ml", "aliases": ["light gbm", "lightgbm algorithm"]},
    {"canonical": "CatBoost", "category": "ai_ml", "aliases": ["catboost algorithm"]},
    {"canonical": "Retrieval-Augmented Generation", "category": "ai_ml", "aliases": ["rag", "retrieval augmented generation"]},
    {"canonical": "LlamaIndex", "category": "ai_ml", "aliases": ["llama index", "gpt index"]},
    {"canonical": "Whisper", "category": "ai_ml", "aliases": ["openai whisper", "whisper asr"]},
    {"canonical": "Stable Diffusion", "category": "ai_ml", "aliases": ["stability ai", "stable-diffusion"]},
    {"canonical": "Vector Database", "category": "ai_ml", "aliases": ["vector search", "vector embeddings", "vector databases"]},
    {"canonical": "Semantic Search", "category": "ai_ml", "aliases": ["neural search", "semantic retrieval"]},
    {"canonical": "LoRA", "category": "ai_ml", "aliases": ["low rank adaptation", "qlora", "peft"]},
    {"canonical": "Gensim", "category": "ai_ml", "aliases": ["gensim library", "word2vec"]},
    {"canonical": "SciPy", "category": "ai_ml", "aliases": ["scipy library", "python scipy"]},

    # data
    {"canonical": "Google BigQuery", "category": "data", "aliases": ["bigquery", "big query", "bq"]},
    {"canonical": "Amazon Redshift", "category": "data", "aliases": ["redshift", "aws redshift"]},
    {"canonical": "Databricks", "category": "data", "aliases": ["databricks lakehouse", "databricks platform"]},
    {"canonical": "Apache Flink", "category": "data", "aliases": ["flink", "apache flink stream"]},
    {"canonical": "Trino", "category": "data", "aliases": ["trino query engine", "prestosql"]},
    {"canonical": "Presto", "category": "data", "aliases": ["prestodb", "presto query"]},
    {"canonical": "Dagster", "category": "data", "aliases": ["dagster orchestrator"]},
    {"canonical": "Prefect", "category": "data", "aliases": ["prefect orchestrator"]},
    {"canonical": "Great Expectations", "category": "data", "aliases": ["great-expectations", "gx data quality"]},
    {"canonical": "Luigi", "category": "data", "aliases": ["spotify luigi"]},

    # testing
    {"canonical": "Vitest", "category": "testing", "aliases": ["vitest framework"]},
    {"canonical": "React Testing Library", "category": "testing", "aliases": ["rtl", "testing-library"]},
    {"canonical": "Mockito", "category": "testing", "aliases": ["mockito framework"]},
    {"canonical": "k6", "category": "testing", "aliases": ["k6 load testing", "grafana k6"]},
    {"canonical": "Locust", "category": "testing", "aliases": ["locust load testing"]},
    {"canonical": "NUnit", "category": "testing", "aliases": ["nunit framework"]},
    {"canonical": "xUnit", "category": "testing", "aliases": ["xunit framework"]},
    {"canonical": "Behave", "category": "testing", "aliases": ["behave bdd", "python behave"]},

    # tools & security
    {"canonical": "Docker Compose", "category": "tools", "aliases": ["docker-compose"]},
    {"canonical": "pnpm", "category": "tools", "aliases": ["pnpm package manager"]},
    {"canonical": "Turborepo", "category": "tools", "aliases": ["turbopack", "turbo repo"]},
    {"canonical": "Postman API", "category": "tools", "aliases": ["newman runner"]},
    {"canonical": "Insomnia", "category": "tools", "aliases": ["insomnia rest"]},
    {"canonical": "OAuth 2.0", "category": "security", "aliases": ["oauth 2", "oauth2.0"]},
    {"canonical": "Identity and Access Management", "category": "security", "aliases": ["iam", "identity management"]},
    {"canonical": "Single Sign-On", "category": "security", "aliases": ["sso", "saml sso"]},
    {"canonical": "SIEM", "category": "security", "aliases": ["security information and event management"]},
    {"canonical": "Vulnerability Assessment", "category": "security", "aliases": ["vulnerability scanning", "vapt"]}
]

def main():
    with open(TAX_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    existing = {s["canonical"].lower() for s in data["skills"]}
    added = 0
    for s in new_skills:
        if s["canonical"].lower() not in existing:
            data["skills"].append(s)
            existing.add(s["canonical"].lower())
            added += 1

    with open(TAX_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"Added {added} skills. Total skills now: {len(data['skills'])}")

if __name__ == "__main__":
    main()
