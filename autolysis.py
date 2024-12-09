import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Ensure the AIPROXY_TOKEN is set
API_URL = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
API_TOKEN = os.getenv("AIPROXY_TOKEN")
if not API_TOKEN:
    print("Error: AIPROXY_TOKEN environment variable is not set.")
    sys.exit(1)

def load_data(file_path):
    """Load the dataset."""
    try:
        # Try reading the file with UTF-8 encoding first
        data = pd.read_csv(file_path, encoding='utf-8')
        print(f"Loaded dataset with {data.shape[0]} rows and {data.shape[1]} columns.")
        return data
    except UnicodeDecodeError:
        # If UTF-8 fails, try reading with ISO-8859-1 encoding
        print("UTF-8 encoding failed, trying ISO-8859-1 encoding.")
        try:
            data = pd.read_csv(file_path, encoding='ISO-8859-1')
            print(f"Loaded dataset with {data.shape[0]} rows and {data.shape[1]} columns.")
            return data
        except Exception as e:
            print(f"Error loading data: {e}")
            sys.exit(1)
    except Exception as e:
        print(f"Error loading data: {e}")
        sys.exit(1)

def analyze_data(data):
    """Perform a generic analysis on the dataset."""
    summary = {
        "Shape": data.shape,
        "Columns": data.dtypes.to_dict(),
        "Missing Values": data.isnull().sum().to_dict(),
        "Summary Statistics": data.describe(include='all').to_dict(),
    }
    return summary

def visualize_data(data, output_prefix):
    """Create visualizations for the dataset."""
    # Select only numeric columns
    numeric_data = data.select_dtypes(include=[np.number])

    # Correlation heatmap (if applicable)
    if numeric_data.shape[1] > 1:
        plt.figure(figsize=(8, 6))
        sns.heatmap(numeric_data.corr(), annot=True, fmt=".2f", cmap="coolwarm")
        plt.title("Correlation Heatmap")
        plt.savefig(f"{output_prefix}_heatmap.png")
        print(f"Saved heatmap as {output_prefix}_heatmap.png")
        plt.close()

    # Distribution of numerical columns
    num_cols = numeric_data.columns
    for col in num_cols:
        plt.figure(figsize=(6, 4))
        sns.histplot(numeric_data[col].dropna(), kde=True)
        plt.title(f"Distribution of {col}")
        plt.savefig(f"{output_prefix}_{col}_distribution.png")
        print(f"Saved distribution plot for {col} as {output_prefix}_{col}_distribution.png")
        plt.close()

def query_llm(prompt):
    """Send a query to the AI Proxy and get the response."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_TOKEN}",
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
    }
    try:
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()  # Raise an exception for HTTP errors
        response_data = response.json()
        return response_data.get("choices", [{}])[0].get("message", {}).get("content", "No response.")
    except requests.exceptions.RequestException as e:
        print(f"Error querying the AI Proxy: {e}")
        sys.exit(1)

def narrate_story(data_summary, visualizations):
    """Generate a narrative for the analysis."""
    prompt = f"""
    You are analyzing a dataset with the following summary:
    {data_summary}
    Visualizations generated include:
    {visualizations}
    Write a story describing the dataset, analysis, insights, and implications.
    """
    return query_llm(prompt)

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py dataset.csv")
        sys.exit(1)
    
    file_path = sys.argv[1]
    data = load_data(file_path)
    summary = analyze_data(data)
    
    # Generate visualizations
    output_prefix = os.path.splitext(file_path)[0]
    visualize_data(data, output_prefix)
    
    # List generated visualizations
    visualizations = [f for f in os.listdir('.') if f.startswith(output_prefix) and f.endswith('.png')]
    
    # Generate a narrative
    story = narrate_story(summary, visualizations)
    
    # Save the story as README.md
    with open("README.md", "w") as readme_file:
        readme_file.write(f"# Automated Analysis of {file_path}\n\n")
        readme_file.write(story + "\n\n")
        for viz in visualizations:
            readme_file.write(f"![{viz}]({viz})\n")
    
    print("Analysis complete. Results saved to README.md and PNG files.")

if __name__ == "__main__":
    main()
