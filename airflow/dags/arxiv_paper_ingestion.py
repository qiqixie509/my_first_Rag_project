from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
from arxiv_ingestion.setup import setup_environment
from arxiv_ingestion.fetching import fetch_daily_papers
from arxiv_ingestion.indexing import index_papers_hybrid
from arxiv_ingestion.reporting import generate_daily_report


default_args = {
    "owner": "arxiv-curator",
    "depends_on_past": False,
    "start_date": datetime(2026, 1, 1),
    "email": ["xieqiqi93@gmail.com"],
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "catchup": False,
}

dag = DAG(
    "arxiv_paper_ingestion",
    default_args=default_args,
    description="Daily arXiv CS.AI paper pipeline: fetch->store to PostgreSQL -> chunk-embed ->hybrid OpenSearch index",
    schedule="0 6 * * 1-5", # run daily at 6:00 AM Monday to Friday
    max_active_runs=1,
    catchup=False,
    tags=["arxiv", "papers", "ingestion", "hybrid-search", "embeddings", "chunks"],
)

setup_tasks = PythonOperator(
    task_id="setup_tasks",
    python_callable=setup_environment,
    dag=dag,
)
    
fetch_task = PythonOperator(
    task_id="fetch_daily_papers",
    python_callable=fetch_daily_papers,
    dag=dag,
)

index_hybrid_task = PythonOperator(
    task_id="index_hybrid_task",
    python_callable=index_papers_hybrid,
    dag=dag,
)

report_task = PythonOperator(
    task_id="generate_daily_report",
    python_callable=generate_daily_report,
    dag=dag,
)

cleanup_task = BashOperator(
    task_id="cleanup_temp_files",
    bash_command="""
        echo "Cleaning up temporary files..."
        # Remove PDFs older than 30 days to manage disk space
        find /tmp -name "*.pdf" -type f -mtime +30 -delete 2>/dev/null || true
        echo "Cleanup completed"
    """,
    dag=dag,
)

setup_tasks >> fetch_task >> index_hybrid_task >> report_task >> cleanup_task

