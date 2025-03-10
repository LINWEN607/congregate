"""
GitLab Import Source User Reassignment Cancellation

This script processes a CSV file containing GitLab import source user data
and calls a GraphQL mutation to cancel user reassignments.

Usage:
    python cancel_reassignments.py <csv_file>

Environment Variables:
    DESTINATION_GITLAB_ROOT: URL of the GitLab instance
    DESTINATION_ADMIN_ACCESS_TOKEN: Access token with admin privileges
"""

import argparse
import csv
import logging
import os
import sys
from datetime import datetime
import requests


def setup_logging():
    """
    Set up logging to both console and a timestamped file.
    
    Returns:
        logging.Logger: Configured logger instance
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"reassignment_cancellation_{timestamp}.log"
    
    logger = logging.getLogger("reassignment_cancellation")
    logger.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # File handler
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.INFO)
    
    # Create formatter and add it to handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


def execute_graphql_mutation(gitlab_url, access_token, import_source_user_id, client_mutation_id, logger):
    """
    Execute GraphQL mutation to cancel import source user reassignment.
    
    Args:
        gitlab_url (str): The GitLab instance URL
        access_token (str): GitLab admin access token
        import_source_user_id (str): The import source user ID
        client_mutation_id (str): Client mutation ID
        logger (logging.Logger): Logger instance
        
    Returns:
        dict: Response from GraphQL API or None if failed
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Construct the GraphQL endpoint URL
    graphql_endpoint = f"{gitlab_url}/api/graphql"
    
    # The GraphQL mutation query
    mutation = """
    mutation ($clientMutationId: String, $importSourceUserId: ImportSourceUserID!) {
      importSourceUserCancelReassignment(
        input: {clientMutationId: $clientMutationId, id: $importSourceUserId}
      ) {
        clientMutationId
        importSourceUser {
          status
          reassignedByUser {
            name
          }
        }
        errors
      }
    }
    """
    
    # Variables for the mutation
    variables = {
        "clientMutationId": client_mutation_id,
        "importSourceUserId": import_source_user_id
    }
    
    # Construct the request payload
    payload = {
        "query": mutation,
        "variables": variables
    }
    
    try:
        response = requests.post(graphql_endpoint, json=payload, headers=headers)
        response.raise_for_status()
        response_data = response.json()
        
        # Check for GraphQL errors
        if "errors" in response_data:
            logger.error(f"GraphQL error for ID {import_source_user_id}: {response_data['errors']}")
            return None
            
        return response_data
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for ID {import_source_user_id}: {str(e)}")
        return None


def process_csv(csv_path, gitlab_url, access_token, logger):
    """
    Process the CSV file and execute GraphQL mutations for each row.
    
    Args:
        csv_path (str): Path to the CSV file
        gitlab_url (str): The GitLab instance URL
        access_token (str): GitLab admin access token
        logger (logging.Logger): Logger instance
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    failed_rows_filename = f"failed_cancellations_{timestamp}.csv"
    
    failed_rows = []
    total_rows = 0
    successful_cancellations = 0
    
    try:
        with open(csv_path, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            
            # Check if required columns exist
            required_columns = ["GitLab importSourceUserId", "GitLab clientMutationId"]
            for column in required_columns:
                if column not in reader.fieldnames:
                    logger.error(f"Required column '{column}' not found in CSV file")
                    sys.exit(1)
                    
            for row in reader:
                total_rows += 1
                import_source_user_id = row["GitLab importSourceUserId"]
                client_mutation_id = row["GitLab clientMutationId"]
                
                if not import_source_user_id:
                    logger.warning(f"Skipping row {total_rows}: Empty import source user ID")
                    failed_rows.append(row)
                    continue
                
                logger.info(f"Processing row {total_rows}: import_source_user_id={import_source_user_id}")
                
                result = execute_graphql_mutation(
                    gitlab_url, 
                    access_token, 
                    import_source_user_id, 
                    client_mutation_id, 
                    logger
                )
                
                if result and "data" in result and result["data"]["importSourceUserCancelReassignment"]:
                    response_data = result["data"]["importSourceUserCancelReassignment"]
                    
                    if response_data["errors"] and len(response_data["errors"]) > 0:
                        logger.error(f"Row {total_rows}: GraphQL mutation returned errors: {response_data['errors']}")
                        failed_rows.append(row)
                    else:
                        successful_cancellations += 1
                        status = response_data["importSourceUser"]["status"] if response_data["importSourceUser"] else "unknown"
                        logger.info(f"Row {total_rows}: Successfully cancelled reassignment. New status: {status}")
                else:
                    logger.error(f"Row {total_rows}: Failed to cancel reassignment")
                    failed_rows.append(row)
                    
        # Write failed rows to a CSV file if there are any
        if failed_rows:
            with open(failed_rows_filename, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=reader.fieldnames)
                writer.writeheader()
                writer.writerows(failed_rows)
                logger.info(f"Wrote {len(failed_rows)} failed rows to {failed_rows_filename}")
        
        logger.info(f"Processing complete. Total rows: {total_rows}, Successful cancellations: {successful_cancellations}, Failed: {len(failed_rows)}")
        
    except FileNotFoundError:
        logger.error(f"CSV file not found: {csv_path}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error processing CSV file: {str(e)}")
        sys.exit(1)


def main():
    """
    Main entry point for the script.
    Parses command-line arguments and initiates CSV processing.
    """
    parser = argparse.ArgumentParser(description='Cancel GitLab import source user reassignments based on CSV data')
    parser.add_argument('csv_file', help='Path to the CSV file containing import source user data')
    args = parser.parse_args()
    
    # Set up logging
    logger = setup_logging()
    
    # Get environment variables
    gitlab_url = os.environ.get('DESTINATION_GITLAB_ROOT')
    access_token = os.environ.get('DESTINATION_ADMIN_ACCESS_TOKEN')
    
    if not gitlab_url:
        logger.error("DESTINATION_GITLAB_ROOT environment variable not set")
        sys.exit(1)
        
    if not access_token:
        logger.error("DESTINATION_ADMIN_ACCESS_TOKEN environment variable not set")
        sys.exit(1)
    
    # Remove trailing slash from GitLab URL if present
    gitlab_url = gitlab_url.rstrip('/')
    
    logger.info(f"Starting import source user reassignment cancellation for {args.csv_file}")
    logger.info(f"Using GitLab instance: {gitlab_url}")
    
    process_csv(args.csv_file, gitlab_url, access_token, logger)


if __name__ == "__main__":
    main()