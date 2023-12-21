import wikipedia

# Prompt the user to enter a search query
search_query = input("Enter a search query: ")

# Search Wikipedia for the query
search_results = wikipedia.search(search_query)

# Display the search results to the user
print("Search Results:")
for i, result in enumerate(search_results):
    print(f"{i+1}. {result}")