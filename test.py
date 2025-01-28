import pandas as pd
from tabulate import tabulate
import matplotlib.pyplot as plt

# Sample DataFrame
data = {
    'Name': ['Alice', 'Bob', 'Charlie'],
    'Age': [25, 30, 35],
    'City': ['New York', 'Los Angeles', 'Chicago']
}

df = pd.read_csv('test.csv')

# Convert DataFrame to character table
table = tabulate(df, headers='keys', tablefmt='rounded_grid')

# Define character dimensions (in pixels)
char_width = 7  # Approximate width of a character in pixels
line_height = 12  # Approximate height of a line in pixels

# Calculate the size of the table
num_lines = table.count('\n') + 1  # Number of lines in the table
num_chars = max(len(line) for line in table.split('\n'))  # Maximum number of characters in a line

# Calculate figure size in inches (1 inch = 100 pixels)
fig_width = num_chars * char_width / 100
fig_height = num_lines * line_height / 100

# Create a figure and axis with calculated size
fig, ax = plt.subplots(figsize=(fig_width, fig_height))

# Hide axes
ax.axis('off')

# Add the table to the axes with adjusted position
ax.text(0.5, 0.5, table, fontsize=10, ha='center', va='center', fontfamily='monospace')

# Save the figure as an image with tight bounding box and no padding
plt.savefig('dataframe_table.png', bbox_inches='tight', dpi=300, pad_inches=0)
plt.close()