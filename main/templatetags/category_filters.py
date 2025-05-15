from django import template

register = template.Library()

CATEGORY_TRANSLATIONS = {
    'snacks': 'Грицки',
    'sweets': 'Слатки',
    'bread': 'Леб и Пекарски Производи',
    'dairy': 'Млеко, Млечни Производи и Јајца',
    'vegetables': 'Зеленчук',
    'fruit': 'Овошје',
    'meat': 'Месо',
    'sauces': 'Сосови и Преливи',
    'basics': 'Основни Производи',
    'drinks': 'Пијалоци - Кафе и Чај',
    'delicacies': 'Деликатесни Производи',
    'tobacco': 'Производи од Тутун',
    'cosmetics': 'Козметика',
    'household': 'Домаќинство',
    'others': 'Останато',
    'pet food': 'Храна за Домашни Миленичиња',
    'home hygiene': 'Средства за Хигиена во Домот',
    'healthy food': 'Здрава Храна',
    'canned food': 'Конзервирана Храна',
    'frozen food': 'Замрзната Храна',
    'baby food': 'Храна за Бебиња',
    # Add all other categories
}

@register.filter(name='translate_category')
def translate_category(category):
    # Convert to lowercase and strip whitespace for reliable matching
    return CATEGORY_TRANSLATIONS.get(category.lower().strip(), category)