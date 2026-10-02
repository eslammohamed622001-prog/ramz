import re
import os
import argparse
import sys

def بناء_الرموز(الكود):
    القواعد = [
        ('كلمة_مفتاحية', r'\b(شكل|صفحة|عنوان|زر|معنى|عند|النقر|على|أظهر|طراز|تنسيق|خاصية|نموذج|حقل_نص|حقل_بريد|حقل_نص_طويل)\b'),
        ('نص_مقتبس', r'"[^"]*"'),
        ('قوس_فتح', r'\{'),
        ('قوس_إغلاق', r'\}'),
        ('عامل', r'='),
        ('تعليق', r'//.*'),
        ('معرّف', r'[أ-يa-zA-Z_][أ-يa-zA-Z0-9_]*'),
        ('مسافة', r'\s+'),
    ]
    نمط_موحد = '|'.join(f'(?P<{اسم}>{قاعدة})' for اسم, قاعدة in القواعد)
    الرموز = []
    for مطابقة in re.finditer(نمط_موحد, الكود):
        نوع = مطابقة.lastgroup
        قيمة = مطابقة.group()
        if نوع and نوع not in ('مسافة', 'تعليق'):
            الرموز.append({'النوع': نوع, 'القيمة': قيمة})
    return الرموز

class محلل_نحوي:
    def __init__(self, الرموز):
        self.الرموز = الرموز
        self.الموضع = 0

    def استهلك(self, النوع_المتوقع, رسالة_خطأ):
        if self.الموضع < len(self.الرموز):
            رمز = self.الرموز[self.الموضع]
            if رمز['النوع'] == النوع_المتوقع or رمز['القيمة'] == النوع_المتوقع:
                self.الموضع += 1
                return رمز
            else:
                raise Exception(f"خطأ نحوي: {رسالة_خطأ}. وجدنا: {رمز['القيمة']}")
        else:
            raise Exception(f"خطأ نحوي: {رسالة_خطأ}. وصلنا لنهاية الملف.")

    def تحليل(self):
        شجرة = {'شكل': None, 'طراز': None, 'معنى': None}
        while self.الموضع < len(self.الرموز):
            رمز = self.الرموز[self.الموضع]
            if رمز['القيمة'] == 'شكل':
                شجرة['شكل'] = self.تحليل_شكل()
            elif رمز['القيمة'] == 'طراز':
                شجرة['طراز'] = self.تحليل_طراز()
            elif رمز['القيمة'] == 'معنى':
                شجرة['معنى'] = self.تحليل_معنى()
            else:
                self.الموضع += 1
        return شجرة

    def تحليل_شكل(self):
        self.استهلك('شكل', "توقع 'شكل'")
        self.استهلك('قوس_فتح', "توقع '{'")
        عقدة = {'النوع': 'شكل', 'الصفحات': []}
        while self.الموضع < len(self.الرموز) and self.الرموز[self.الموضع]['النوع'] != 'قوس_إغلاق':
            عقدة['الصفحات'].append(self.تحليل_صفحة())
        self.استهلك('قوس_إغلاق', "توقع '}'")
        return عقدة

    def تحليل_صفحة(self):
        self.استهلك('صفحة', "توقع 'صفحة'")
        اسم_الصفحة = self.استهلك('نص_مقتبس', "توقع اسم الصفحة")['القيمة'].strip('"')
        self.استهلك('قوس_فتح', "توقع '{'")
        عقدة = {'النوع': 'صفحة', 'الاسم': اسم_الصفحة, 'المحتوى': []}
        while self.الموضع < len(self.الرموز) and self.الرموز[self.الموضع]['النوع'] != 'قوس_إغلاق':
            رمز = self.الرموز[self.الموضع]
            if رمز['القيمة'] == 'عنوان':
                عقدة['المحتوى'].append(self.تحليل_عنصر('عنوان'))
            elif رمز['القيمة'] == 'زر':
                عقدة['المحتوى'].append(self.تحليل_عنصر('زر'))
            elif رمز['القيمة'] == 'نموذج':
                عقدة['المحتوى'].append(self.تحليل_نموذج())
            else:
                self.الموضع += 1
        self.استهلك('قوس_إغلاق', "توقع '}'")
        return عقدة

    def تحليل_عنصر(self, نوع_العنصر):
        self.استهلك(نوع_العنصر, f"توقع '{نوع_العنصر}'")
        رمز = self.استهلك('نص_مقتبس', "توقع نص")
        return {'النوع': نوع_العنصر, 'النص': رمز['القيمة'].strip('"')}

    def تحليل_نموذج(self):
        self.استهلك('نموذج', "توقع 'نموذج'")
        اسم_النموذج = self.استهلك('نص_مقتبس', "توقع اسم النموذج")['القيمة'].strip('"')
        self.استهلك('قوس_فتح', "توقع '{'")
        حقول = []
        while self.الموضع < len(self.الرموز) and self.الرموز[self.الموضع]['النوع'] != 'قوس_إغلاق':
            رمز = self.الرموز[self.الموضع]
            if رمز['القيمة'] == 'حقل_نص':
                self.استهلك('حقل_نص', "توقع 'حقل_نص'")
                المعرف = self.استهلك('نص_مقتبس', "توقع المعرف")['القيمة'].strip('"')
                النص_البديل = self.استهلك('نص_مقتبس', "توقع النص البديل")['القيمة'].strip('"')
                حقول.append({'النوع': 'حقل_نص', 'المعرف': المعرف, 'النص_البديل': النص_البديل})
            elif رمز['القيمة'] == 'حقل_بريد':
                self.استهلك('حقل_بريد', "توقع 'حقل_بريد'")
                المعرف = self.استهلك('نص_مقتبس', "توقع المعرف")['القيمة'].strip('"')
                النص_البديل = self.استهلك('نص_مقتبس', "توقع النص البديل")['القيمة'].strip('"')
                حقول.append({'النوع': 'حقل_بريد', 'المعرف': المعرف, 'النص_البديل': النص_البديل})
            elif رمز['القيمة'] == 'حقل_نص_طويل':
                self.استهلك('حقل_نص_طويل', "توقع 'حقل_نص_طويل'")
                المعرف = self.استهلك('نص_مقتبس', "توقع المعرف")['القيمة'].strip('"')
                النص_البديل = self.استهلك('نص_مقتبس', "توقع النص البديل")['القيمة'].strip('"')
                حقول.append({'النوع': 'حقل_نص_طويل', 'المعرف': المعرف, 'النص_البديل': النص_البديل})
            elif رمز['القيمة'] == 'زر':
                حقول.append(self.تحليل_عنصر('زر'))
            else:
                self.الموضع += 1
        self.استهلك('قوس_إغلاق', "توقع '}'")
        return {'النوع': 'نموذج', 'الاسم': اسم_النموذج, 'الحقول': حقول}

    def تحليل_طراز(self):
        self.استهلك('طراز', "توقع 'طراز'")
        self.استهلك('قوس_فتح', "توقع '{'")
        عقدة = {'النوع': 'طراز', 'القواعد': []}
        while self.الموضع < len(self.الرموز) and self.الرموز[self.الموضع]['النوع'] != 'قوس_إغلاق':
            عقدة['القواعد'].append(self.تحليل_تنسيق())
        self.استهلك('قوس_إغلاق', "توقع '}'")
        return عقدة

    def تحليل_تنسيق(self):
        self.استهلك('تنسيق', "توقع 'تنسيق'")
        الهدف = self.استهلك('نص_مقتبس', "توقع اسم العنصر")['القيمة'].strip('"')
        self.استهلك('قوس_فتح', "توقع '{'")
        خصائص = {}
        while self.الموضع < len(self.الرموز) and self.الرموز[self.الموضع]['النوع'] != 'قوس_إغلاق':
            self.استهلك('خاصية', "توقع 'خاصية'")
            اسم_الخاصية = self.استهلك('نص_مقتبس', "توقع اسم الخاصية")['القيمة'].strip('"')
            self.استهلك('عامل', "توقع '='")
            قيمة_الخاصية = self.استهلك('نص_مقتبس', "توقع قيمة الخاصية")['القيمة'].strip('"')
            خصائص[اسم_الخاصية] = قيمة_الخاصية
        self.استهلك('قوس_إغلاق', "توقع '}'")
        return {'الهدف': الهدف, 'الخصائص': خصائص}

    def تحليل_معنى(self):
        self.استهلك('معنى', "توقع 'معنى'")
        self.استهلك('قوس_فتح', "توقع '{'")
        عقدة = {'النوع': 'معنى', 'البيانات': []}
        while self.الموضع < len(self.الرموز) and self.الرموز[self.الموضع]['النوع'] != 'قوس_إغلاق':
            عقدة['البيانات'].append(self.تحليل_بيان())
        self.استهلك('قوس_إغلاق', "توقع '}'")
        return عقدة

    def تحليل_بيان(self):
        رمز = self.الرموز[self.الموضع]
        if رمز['القيمة'] == 'عند':
            return self.تحليل_حدث()
        elif رمز['القيمة'] == 'أظهر':
            return self.تحليل_طباعة()
        else:
            self.الموضع += 1
            return None

    def تحليل_حدث(self):
        self.استهلك('عند', "توقع 'عند'")
        self.استهلك('النقر', "توقع 'النقر'")
        self.استهلك('على', "توقع 'على'")
        رمز_الاسم = self.استهلك('نص_مقتبس', "توقع اسم الزر")
        اسم_الزر = رمز_الاسم['القيمة'].strip('"')
        self.استهلك('قوس_فتح', "توقع '{'")
        الأوامر = []
        while self.الموضع < len(self.الرموز) and self.الرموز[self.الموضع]['النوع'] != 'قوس_إغلاق':
            أمر = self.تحليل_أمر()
            if أمر:
                الأوامر.append(أمر)
        self.استهلك('قوس_إغلاق', "توقع '}'")
        return {'النوع': 'حدث', 'الحدث': 'نقر', 'الهدف': اسم_الزر, 'الأوامر': الأوامر}

    def تحليل_أمر(self):
        رمز = self.الرموز[self.الموضع]
        if رمز['القيمة'] == 'أظهر':
            return self.تحليل_طباعة()
        else:
            self.الموضع += 1
            return None

    def تحليل_طباعة(self):
        self.استهلك('أظهر', "توقع 'أظهر'")
        النص = self.استهلك('نص_مقتبس', "توقع نص")['القيمة'].strip('"')
        return {'النوع': 'طباعة', 'النص': النص}

def توليد_أمر(أمر):
    if أمر['النوع'] == 'طباعة':
        return f'            alert("{أمر["النص"]}");'
    return ''

def توليد_الكود(شجرة):
    html = []
    html.append('<!DOCTYPE html>')
    html.append('<html lang="ar" dir="rtl">')
    html.append('<head>')
    html.append('    <meta charset="UTF-8">')
    html.append('    <meta name="viewport" content="width=device-width, initial-scale=1.0">')
    html.append('    <title>رَمْز - مشروع تجريبي</title>')
    html.append('    <style>')
    html.append('        body { font-family: "Cairo", "Tajawal", sans-serif; background: #0B0C10; color: #C5C6C7; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }')
    html.append('        .container { text-align: center; padding: 40px; max-width: 600px; width: 100%; }')
    html.append('        input, textarea { width: 100%; padding: 12px; margin: 10px 0; border-radius: 8px; border: 2px solid #D4AF37; background: #1A1C23; color: white; font-family: inherit; font-size: 1em; box-sizing: border-box; }')
    html.append('        input:focus, textarea:focus { outline: none; border-color: #FFB347; }')
    html.append('        textarea { min-height: 120px; resize: vertical; }')
    html.append('        button { padding: 12px 30px; margin-top: 15px; cursor: pointer; font-family: inherit; font-size: 1em; }')
    
    خريطة_الخصائص = {"اللون": "color", "الخلفية": "background-color", "الحجم": "font-size", "المحاذاة": "text-align", "الحواف": "border-radius"}
    
    if شجرة.get('طراز'):
        for قاعدة in شجرة['طراز'].get('القواعد', []):
            الهدف = قاعدة['الهدف']
            محدد = 'h1' if الهدف == 'عنوان' else 'button'
            html.append(f'        {محدد} {{')
            for اسم_عربي, قيمة in قاعدة['الخصائص'].items():
                اسم_انجليزي = خريطة_الخصائص.get(اسم_عربي, اسم_عربي)
                if اسم_عربي == "المحاذاة" and قيمة == "وسط": قيمة = "center"
                html.append(f'            {اسم_انجليزي}: {قيمة};')
            html.append('        }')
            
    html.append('    </style></head><body>')
    
    if شجرة.get('شكل'):
        for صفحة in شجرة['شكل'].get('الصفحات', []):
            html.append('    <div class="container">')
            for عنصر in صفحة.get('المحتوى', []):
                if عنصر['النوع'] == 'عنوان':
                    html.append(f'        <h1>{عنصر["النص"]}</h1>')
                elif عنصر['النوع'] == 'نموذج':
                    html.append(f'        <form id="{عنصر["الاسم"]}">')
                    for حقل in عنصر['الحقول']:
                        if حقل['النوع'] == 'حقل_نص':
                            html.append(f'            <input type="text" id="{حقل["المعرف"]}" placeholder="{حقل["النص_البديل"]}">')
                        elif حقل['النوع'] == 'حقل_بريد':
                            html.append(f'            <input type="email" id="{حقل["المعرف"]}" placeholder="{حقل["النص_البديل"]}">')
                        elif حقل['النوع'] == 'حقل_نص_طويل':
                            html.append(f'            <textarea id="{حقل["المعرف"]}" placeholder="{حقل["النص_البديل"]}"></textarea>')
                        elif حقل['النوع'] == 'زر':
                            html.append(f'            <button type="button" id="btn-{حقل["النص"]}">{حقل["النص"]}</button>')
                    html.append('        </form>')
            html.append('    </div>')
    
    if شجرة.get('معنى'):
        html.append('    <script>')
        for بيان in شجرة['معنى'].get('البيانات', []):
            if بيان and بيان['النوع'] == 'حدث' and بيان['الحدث'] == 'نقر':
                html.append(f'        document.getElementById("btn-{بيان["الهدف"]}").addEventListener("click", function() {{')
                for أمر in بيان['الأوامر']:
                    if أمر:
                        html.append(توليد_أمر(أمر))
                html.append('        });')
        html.append('    </script>')
    
    html.append('</body></html>')
    return '\n'.join(html)

def رئيسي():
    محلل_الأوامر = argparse.ArgumentParser(description="مترجم لغة رَمْز", formatter_class=argparse.RawTextHelpFormatter)
    محلل_الأوامر.add_argument('--version', action='version', version='رَمْز الإصدار 1.7.0 (دعم النماذج)')
    الأوامر_الفرعية = محلل_الأوامر.add_subparsers(dest='الأمر')
    أمر_البناء = الأوامر_الفرعية.add_parser('build')
    أمر_البناء.add_argument('ملف_الإدخال', nargs='?', default='examples/test.ramz')
    أمر_البناء.add_argument('-o', '--مخرج', default='output/index.html')
    الوسائط = محلل_الأوامر.parse_args()

    if الوسائط.الأمر == 'build':
        if not os.path.exists(الوسائط.ملف_الإدخال):
            print(f"❌ خطأ: الملف غير موجود")
            sys.exit(1)
        with open(الوسائط.ملف_الإدخال, "r", encoding="utf-8") as ملف:
            كود_مصدري = ملف.read()
        try:
            الرموز = بناء_الرموز(كود_مصدري)
            الشجرة = محلل_نحوي(الرموز).تحليل()
            os.makedirs(os.path.dirname(الوسائط.مخرج), exist_ok=True)
            with open(الوسائط.مخرج, "w", encoding="utf-8") as ملف_المخرج:
                ملف_المخرج.write(توليد_الكود(الشجرة))
            print("🎉 تم بناء المشروع بنجاح! افتح output/index.html في المتصفح.")
        except Exception as خطأ:
            print(f" خطأ: {خطأ}")

if __name__ == "__main__":
    رئيسي()