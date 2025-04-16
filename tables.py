import mdpd
import tabulate
import matplotlib.pyplot as plt

CHAR_WIDTH = 7
LINE_HEIGHT = 12

PIXELS_PER_INCH = 100

def code_to_table(code: str):
    df = mdpd.from_md(code)
    table = tabulate.tabulate(df, headers='keys', tablefmt='rounded_grid', showindex=False, maxcolwidths=40)
    return table

def text_to_image(text: str, path: str):
    num_lines = text.count('\n') + 1
    num_chars = max(len(line) for line in text.split('\n'))

    fig_width = num_chars * CHAR_WIDTH / PIXELS_PER_INCH
    fig_height = num_lines * LINE_HEIGHT / PIXELS_PER_INCH

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    fig.set_facecolor('#0b141e')
    ax.axis('off')
    ax.text(0.5, 0.5, text, fontsize=10, ha='center', va='center', fontfamily='monospace', color='#aed1f3')

    plt.savefig(path, bbox_inches='tight', dpi=300, pad_inches=0)

def render_table(table_content: str, path: str):
    """
    `table_content` - markdown representation of the table as a string
    """
    table = code_to_table(table_content)
    text_to_image(table, path)

def main():
    csv = """
| Символ | Описание                     |
|--------|------------------------------|
| \\n   | Перевод строки               |
| \\t   | Табуляция                    |
| \\r   | Возврат каретки              |
| \\a   | Звуковой сигнал (bell)       |
| \\\\   | Обратный слэш                 |
| \\'   | Одинарная кавычка            |
| \\"   | Двойная кавычка              |
| \\b   | Удаление символа (backspace) |
| \\f   | Перевод страницы (form feed) |
| \\v   | Вертикальная табуляция       |
| \\0   | Нулевой байт                 |
"""
    render_table(csv, "yey.png")

if __name__ == "__main__":
    main()