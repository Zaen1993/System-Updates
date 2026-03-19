import kivy
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout

class SystemUpdateApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical')
        label = Label(text="تحديث النظام قيد التثبيت...\nيرجى الانتظار", font_size='20sp')
        button = Button(text="تأكيد", size_hint=(1, 0.2))
        layout.add_widget(label)
        layout.add_widget(button)
        return layout

if __name__ == '__main__':
    SystemUpdateApp().run()
