# libraries used
#!pip install tabula-py
#!pip install fitz
#!pip install pymupdf

# importing libraries
import re
import tabula
import pandas as pd
import numpy as np
import fitz

#data extracction and clening
def extractandclean_table_data(pdf_path):
  """
    Extracts and cleans data from a table in a PDF and saves as a list and
    detect tables of the lenders listings first column returning a list cleaned
    and a dictionary with numeber of page and type of lender

    Args:
        pdf_path: Path to the input PDF file.
  """
  list_extracted = []
  try:
    with fitz.open(pdf_path) as doc:
          target_pages = []
          Lender_Listings = {}
          # Extract data from each page
          for page_num in range(len(doc)):
            tablas = tabula.read_pdf(pdf_path, pages=page_num+1, multiple_tables=True) #search tables on each page
            if not tablas:
              continue
            tabla = tablas[0]
            if re.match(r"Lender Name and Contact Info( Type)?",str(tabla.columns[0])):
              target_pages.append(page_num+1)
              page = doc.load_page(page_num)  # number of page
              page_text = page.get_text("text",sort = True) #identify text and sort it
              words = page_text.splitlines()
              palabra = re.search(r"([A-Z][a-z]+\s)?[A-Z][a-z]+",str(words[0])) #extract all header words
              Lender_Listings[page_num+1] = palabra.group(0) # add to dicctionary
  except FileNotFoundError:
        print(f"Error: PDF file not found at {pdf_path}")
  except Exception as e:
        print(f"An error occurred: {e}")

  #regular expresion to filter and clean data
  name_pattern = r"\b(Lender Name and Contact Info(\s+Type)?|^Bank)\b" #filter

  try:
    for page in target_pages:
          tables = tabula.read_pdf(pdf_path, pages=page, multiple_tables=True)
          first_table = tables[0]
          first_column_data = first_table.iloc[:, 0].dropna().tolist() # clean data from na's
          for data in first_column_data:
            if re.match(name_pattern,str(data)):
              first_column_data.remove(data)
          list_extracted.append(first_column_data)
  except IndexError:
    print("Data cleaning processing")

  return list_extracted, Lender_Listings

# prompt: make a function that recibe a list and a dictionary with keys as pages and values as types of lender and classify the list as Lender Name, Website, Contact Number, and Email (must deal with missing data) using the dictionary to add the Type of lender afterward it returns a CSV with these columns.

def classify_and_export(data_list, lender_dict):
    """
    Classifies a list of data into Lender Name, Website, Contact Number, and Email,
    adds the Type of Lender, and exports the data to a CSV file.

    Args:
        data_list: A list of data to classify.
        lender_dict: A dictionary with page numbers as keys and lender types as values.
    """
    num_page = list(lender_dict.keys())
    classified_data = []
    i = 0

    # Define regular expressions for each category
    name_pattern = r"^\b(?!Lender Name and Contact Info( Type)?|^Bank)\b" # Matches names of firms or companies excluding "Lender Name and Contact Info"
    website_pattern = r"(?:www\.)?[\w-]+\.[\w.-]+"  # Matches websites
    contact_number_pattern = r"([A-Z][a-z]+(\s+[A-Z].+)?)?\s*(\w+@\w+\.\w+)?\s*\((\d{3}\)|\d{3})\s?\d{3}-\d{4}" # Matches contact numbers like "Jhon Dan (###) ###-####" and includes email
    email_pattern = r"[\w\.-]+@[\w\.-]+\.\w{2,5}"  # Matches email addresses

    for page_data in data_list:
        # Determine lender type based on the page number
        lender_type = lender_dict[num_page[i]]
        i += 1
                    # Initialize data fields
        verifyer = {
        'lender_name' : ""
        ,'website' : ""
        ,'contact_number' : ""
        ,'email' : ""
        }

        for iter,item in enumerate(page_data): # iter takes index values

            # Attempt to extract data (handle potential missing data gracefully)
            try:
                if isinstance(item, str):
                  print(f"Processing item: {item}")
                  if re.match(email_pattern,item):
                        verifyer['email'] = page_data[iter]

                  elif re.match(website_pattern,item):
                        verifyer['website'] = page_data[iter]

                  elif re.match(contact_number_pattern,page_data[iter]):
                         verifyer['contact_number'] = page_data[iter]

                  elif re.match(name_pattern,item):
                        print(f"lender name",{item})
                        nombre = re.sub(r"\b(?:Lender|Direct|Private|  Bank|REIT|Correspondent)\b|\d+K|\d+M","",str(page_data[iter]))
                        verifyer['lender_name'] = nombre
                        if verifyer['lender_name'] == "":
                          verifyer['lender_name'] = item
                else:
                    print(f"Unexpected data type: {type(item)}")
            except Exception as e:
                print(f"Error processing item: {item}, Error: {e}")


            #detect where are name data
            if verifyer['email'] != "":
              for key in verifyer.keys():
                if verifyer[key] == "":
                  verifyer[key] = "missing"
            elif verifyer['website'] != "" and all([not re.match(website_pattern,page_data[iter+1]) ,not "@" in page_data[iter+1], not re.match(contact_number_pattern,page_data[iter+1])]): # detect if next item is lender name
              for key in verifyer.keys():
                if verifyer[key] == "":
                  verifyer[key] = "missing"
            elif verifyer['contact_number'] != "" and all([not re.match(website_pattern,page_data[iter+1]) ,not "@" in page_data[iter+1], not re.match(contact_number_pattern,page_data[iter+1])]): # detect if next item is lender name
              for key in verifyer.keys():
                if verifyer[key] == "":
                  verifyer[key] = "missing"
            else:
              continue  # Skip if all fields are empty'''

            classified_data.append([verifyer['lender_name'], verifyer['website'], verifyer['contact_number'], verifyer['email'], lender_type])
            # Initialize data fields again
            verifyer = {
            'lender_name' : ""
            ,'website' : ""
            ,'contact_number' : ""
            ,'email' : ""
            }
    # Create a Pandas DataFrame
    df = pd.DataFrame(classified_data, columns=["Lender Name", "Website", "Contact Number", "Email", "Type Lender"])

    # Export the DataFrame to a CSV file
    df.to_csv("classified_lenders.csv", index=False, encoding='utf-8')  # Specify encoding to handle special characters
    print("Data classified and exported to 'classified_lenders.csv'")

# prompt: make a function that recibe a list and a dictionary with keys as pages and values as types of lender and classify the list as Lender Name, Website, Contact Number, and Email (must deal with missing data) using the dictionary to add the Type of lender afterward it returns a CSV with these columns.

def classify_and_export(data_list, lender_dict):
    """
    Classifies a list of data into Lender Name, Website, Contact Number, and Email,
    adds the Type of Lender, and exports the data to a CSV file.

    Args:
        data_list: A list of data to classify.
        lender_dict: A dictionary with page numbers as keys and lender types as values.
    """
    num_page = list(lender_dict.keys())
    classified_data = []
    i = 0

    # Define regular expressions for each category
    name_pattern = r"^\b(?!Lender Name and Contact Info( Type)?|^Bank)\b" # Matches names of firms or companies excluding "Lender Name and Contact Info"
    website_pattern = r"(?:www\.)?[\w-]+\.[\w.-]+"  # Matches websites
    contact_number_pattern = r"([A-Z][a-z]+(\s+[A-Z].+)?)?\s*(\w+@\w+\.\w+)?\s*\((\d{3}\)|\d{3})\s?\d{3}-\d{4}" # Matches contact numbers like "Jhon Dan (###) ###-####" and includes email
    email_pattern = r"[\w\.-]+@[\w\.-]+\.\w{2,5}"  # Matches email addresses

    for page_data in data_list:
        # Determine lender type based on the page number
        lender_type = lender_dict[num_page[i]]
        i += 1
                    # Initialize data fields
        verifyer = {
        'lender_name' : ""
        ,'website' : ""
        ,'contact_number' : ""
        ,'email' : ""
        }

        for iter,item in enumerate(page_data): # iter takes index values

            # Attempt to extract data (handle potential missing data gracefully)
            try:
                if isinstance(item, str):
                  #print(f"Processing item: {item}")
                  if re.match(email_pattern,item):
                        verifyer['email'] = page_data[iter]

                  elif re.match(website_pattern,item):
                        verifyer['website'] = page_data[iter]

                  elif re.match(contact_number_pattern,page_data[iter]):
                         verifyer['contact_number'] = page_data[iter]

                  elif re.match(name_pattern,item):
                        #print(f"lender name",{item})
                        nombre = re.sub(r"\b(?:Lender|Direct|Private|  Bank|REIT|Correspondent)\b|\d+K|\d+M","",str(page_data[iter]))
                        verifyer['lender_name'] = nombre
                        if verifyer['lender_name'] == "":
                          verifyer['lender_name'] = item
                else:
                    print(f"Unexpected data type: {type(item)}")
            except Exception as e:
                print(f"Error processing item: {item}, Error: {e}")


            #detect where are name data
            if verifyer['email'] != "":
              for key in verifyer.keys():
                if verifyer[key] == "":
                  verifyer[key] = "missing"
            elif verifyer['website'] != "" and all([not re.match(website_pattern,page_data[iter+1]) ,not "@" in page_data[iter+1], not re.match(contact_number_pattern,page_data[iter+1])]): # detect if next item is lender name
              for key in verifyer.keys():
                if verifyer[key] == "":
                  verifyer[key] = "missing"
            elif verifyer['contact_number'] != "" and all([not re.match(website_pattern,page_data[iter+1]) ,not "@" in page_data[iter+1], not re.match(contact_number_pattern,page_data[iter+1])]): # detect if next item is lender name
              for key in verifyer.keys():
                if verifyer[key] == "":
                  verifyer[key] = "missing"
            else:
              continue  # Skip if all fields are empty'''

            classified_data.append([verifyer['lender_name'], verifyer['website'], verifyer['contact_number'], verifyer['email'], lender_type])
            # Initialize data fields again
            verifyer = {
            'lender_name' : ""
            ,'website' : ""
            ,'contact_number' : ""
            ,'email' : ""
            }
    
    # Create a Pandas DataFrame
    df = pd.DataFrame(classified_data, columns=["Lender Name", "Website", "Contact Number", "Email", "Type Lender"])

    # Export the DataFrame to a CSV file
    df.to_csv("classified_lenders.csv", index=False, encoding='utf-8')  # Specify encoding to handle special characters
    print("Data classified and exported to 'classified_lenders.csv'")
