from django import template

register = template.Library()


@register.filter
def get_committee_icon(committee_name):
    icon_mapping = {
        'اللجنة الثقافية': 'fa-bullseye',
        'اللجنة الإعلامية': 'fa-video',
        'اللجنة الشرعية': 'fa-quran',
        'اللجنة التشغيلية لبرنامج حفظ القرآن الكريم المتكامل': 'fa-tasks',
        'اللجنة الرياضية': 'fa-futbol',
        'اللجنة العلمية للقرآن الكريم': 'fa-book',
        'default': 'fa-users'
    }

    return icon_mapping.get(committee_name, icon_mapping['default'])