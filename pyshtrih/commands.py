# -*- coding: utf-8 -*-


import sys
import time
import inspect

from . import misc, excepts


def state(self):
    """
    Состояние ККМ в коротком виде.
    """

    return self.protocol.command(
        0x10,
        self.password
    )


state.cmd = 0x10


def full_state(self):
    """
    Состояние ККМ.
    """

    return self.protocol.command(
        0x11,
        self.password
    )


full_state.cmd = 0x11


def beep(self):
    """
    Гудок.
    """

    return self.protocol.command(
        0x13,
        self.password
    )


beep.cmd = 0x13


def set_exchange_params(self, port, baudrate, timeout):
    """
    Установка параметров обмена.
    """

    return self.protocol.command(
        0x14,
        self.admin_password,
        misc.CAST_SIZE['1'](port),
        misc.CAST_SIZE['1'](misc.BAUDRATE_DIRECT[baudrate]),
        misc.CAST_SIZE['1'](misc.cast_byte_timeout(timeout))
    )


set_exchange_params.cmd = 0x14


def read_exchange_params(self, port):
    """
    Чтение параметров обмена.
    """

    return self.protocol.command(
        0x15,
        self.admin_password,
        misc.CAST_SIZE['1'](port)
    )


read_exchange_params.cmd = 0x15


def reset_settings(self):
    """
    Технологическое обнуление.
    """

    return self.protocol.command_nopass(
        0x16
    )


reset_settings.cmd = 0x16


def print_string(self, string, control_tape=True, cash_tape=True):
    """
    Печать строки.
    """

    control = 0b01 if control_tape else 0b00
    cash = 0b10 if cash_tape else 0b00

    self.wait_printing()
    return self.protocol.command(
        0x17,
        self.password,
        misc.CAST_SIZE['1'](control + cash),
        misc.prepare_string(string, self.DEFAULT_MAX_LENGTH)
    )


print_string.cmd = 0x17


def print_font(self, string, font_num=1, control_tape=True, cash_tape=True):
    """
    Печать строки заданным шрифтом.
    """

    control = 0b01 if control_tape else 0b00
    cash = 0b10 if cash_tape else 0b00

    self.wait_printing()
    return self.protocol.command(
        0x2F,
        self.password,
        misc.CAST_SIZE['1'](control + cash),
        misc.CAST_SIZE['1'](font_num),
        misc.prepare_string(string, self.DEFAULT_MAX_LENGTH)
    )


print_font.cmd = 0x2F


def print_line(self, symbol='-', control_tape=True, cash_tape=True):
    """
    Печать строки-разделителя.
    """

    return self.print_string(symbol * self.DEFAULT_MAX_LENGTH, control_tape, cash_tape)


print_string.related = (print_line,)


def test_start(self, minute):
    """
    Тестовый прогон.
    """

    self.wait_printing()
    return self.protocol.command(
        0x19,
        self.password,
        misc.CAST_SIZE['1'](minute)
    )


test_start.cmd = 0x19


def request_monetary_register(self, num):
    """
    Запрос денежного регистра.
    """

    return self.protocol.command(
        0x1A,
        self.password,
        misc.CAST_SIZE['1'](num)
    )


request_monetary_register.cmd = 0x1A


def request_operational_register(self, num):
    """
    Запрос операционного регистра.
    """

    return self.protocol.command(
        0x1B,
        self.password,
        misc.CAST_SIZE['1'](num)
    )


request_operational_register.cmd = 0x1B


def write_table(self, table, row, field, value, _type):
    """
    Запись таблицы.
    """

    cast_funcs_map = {
        int: misc.FuncChain(bytearray, misc.int_to_bytes),
        str: misc.prepare_string
        # str: misc.encode
        # str был изменен обработчик на prepare_string, т.к. при записи остаток байтов заполнялся другими данными
        # https://github.com/oleg-golovanov/pyshtrih/pull/11/commits/516ab7b417b447881bcd51d30345cf0ceafccb49
    }

    return self.protocol.command(
        0x1E,
        self.admin_password,
        misc.CAST_SIZE['121'](table, row, field),
        cast_funcs_map[_type](value)
    )


write_table.cmd = 0x1E


def read_table(self, table, row, field, _type):
    """
    Чтение таблицы.
    """

    cast_funcs_map = {
        int: misc.bytes_to_int,
        str: misc.FuncChain(misc.decode, misc.bytearray_strip)
    }

    if _type not in (cast_funcs_map.keys()):
        raise ValueError(
            # u'ожидаемые типы {}'.format(', '.join(cast_funcs_map.keys()))
            # edited with https://github.com/oleg-golovanov/pyshtrih/pull/3/commits/3ec33cc5325622babde3cf1894a458b7ce635263
            u'ожидаемые типы {}'.format(', '.join([str(item) for item in cast_funcs_map.keys()]))
        )

    result = self.protocol.command(
        0x1F,
        self.admin_password,
        misc.CAST_SIZE['121'](table, row, field)
    )
    result[u'Значение'] = cast_funcs_map[_type](result[u'Значение'])

    return result


read_table.cmd = 0x1F


def set_time(self, time_):
    """
    Программирование времени.
    """

    # TODO: разобраться с округлением секунд до 00
    return self.protocol.command(
        0x21,
        self.admin_password,
        misc.CAST_SIZE['111'](time_.hour, time_.minute, time_.second)
    )


set_time.cmd = 0x21


def set_date(self, date):
    """
    Программирование даты.
    """

    return self.protocol.command(
        0x22,
        self.admin_password,
        misc.CAST_SIZE['111'](date.day, date.month, date.year - 2000)
    )


set_date.cmd = 0x22


def confirm_date(self, date):
    """
    Подтверждение программирование даты.
    """

    return self.protocol.command(
        0x23,
        self.admin_password,
        misc.CAST_SIZE['111'](date.day, date.month, date.year - 2000)
    )


confirm_date.cmd = 0x23


def set_datetime(self, datetime):
    """
    Установка даты и времени.
    """

    self.set_time(datetime.time())
    self.set_date(datetime.date())
    self.confirm_date(datetime.date())


set_time.related = (set_datetime,)
set_date.related = (set_datetime,)
confirm_date.related = (set_datetime,)
set_datetime.required = (set_time, set_date, confirm_date)


def init_table(self):
    """
    Инициализация таблиц начальными значениями
    """

    return self.protocol.command(
        0x24,
        self.admin_password
    )


init_table.cmd = 0x24


def cut(self, partial=False):
    """
    Обрезка чека.
    """

    self.wait_printing()
    return self.protocol.command(
        0x25,
        self.password,
        misc.CAST_SIZE['1'](partial)
    )


cut.cmd = 0x25


def reset_summary(self):
    """
    Общее гашение
    """

    return self.protocol.command(
        0x27,
        self.admin_password
    )


reset_summary.cmd = 0x27


def open_drawer(self, box=0):
    """
    Открыть денежный ящик.
    """

    return self.protocol.command(
        0x28,
        self.password,
        misc.CAST_SIZE['1'](box)
    )


open_drawer.cmd = 0x28


def feed(self, count, control_tape=False, cash_tape=False, skid_document=False):
    """
    Протяжка чековой ленты на заданное количество строк.
    """

    if count > 255:
        raise ValueError(u'Количество строк должно быть меньше 255')

    control = 0b001 if control_tape else 0b000
    cash = 0b010 if cash_tape else 0b000
    skid = 0b100 if skid_document else 0b000

    self.wait_printing()
    return self.protocol.command(
        0x29,
        self.password,
        misc.CAST_SIZE['1'](control + cash + skid),
        misc.CAST_SIZE['1'](count)
    )


feed.cmd = 0x29


def test_stop(self):
    """
    Прерывание тестового прогона.
    """

    self.wait_printing()
    return self.protocol.command(
        0x2B,
        self.password
    )


test_stop.cmd = 0x2B


def request_table_structure(self, table):
    """
    Запрос структуры таблицы.
    """

    return self.protocol.command(
        0x2D,
        self.admin_password,
        misc.CAST_SIZE['1'](table)
    )


request_table_structure.cmd = 0x2D


def request_field_structure(self, table, field):
    """
    Запрос структуры поля.
    """

    return self.protocol.command(
        0x2E,
        self.admin_password,
        misc.CAST_SIZE['11'](table, field)
    )


request_field_structure.cmd = 0x2E


def x_report(self):
    """
    Суточный отчет без гашения.
    """

    self.wait_printing()
    return self.protocol.command(
        0x40,
        self.admin_password
    )


x_report.cmd = 0x40


def z_report(self):
    """
    Суточный отчет с гашением.
    """

    self.wait_printing()
    return self.protocol.command(
        0x41,
        self.admin_password
    )


z_report.cmd = 0x41


def sections_report(self):
    """
    Отчёт по секциям.
    """

    self.wait_printing()
    return self.protocol.command(
        0x42,
        self.admin_password
    )


sections_report.cmd = 0x42


def income(self, cash):
    """
    Внесение.
    """

    self.wait_printing()
    return self.protocol.command(
        0x50,
        self.password,
        misc.CAST_SIZE['11111'](*misc.int_to_bytes(cash, 5))
    )


income.cmd = 0x50


def outcome(self, cash):
    """
    Выплата.
    """

    self.wait_printing()
    return self.protocol.command(
        0x51,
        self.password,
        misc.CAST_SIZE['11111'](*misc.int_to_bytes(cash, 5))
    )


outcome.cmd = 0x51


def sale(self, item, department_num=0, tax1=0, tax2=0, tax3=0, tax4=0):
    """
    Продажа.
    """

    text, quantity, price = item

    try:
        return self.protocol.command(
            0x80,
            self.password,
            misc.CAST_SIZE['11111'](*misc.int_to_bytes(quantity, 5)),
            misc.CAST_SIZE['11111'](*misc.int_to_bytes(price, 5)),
            misc.CAST_SIZE['1'](department_num),
            misc.CAST_SIZE['1111'](tax1, tax2, tax3, tax4),
            misc.prepare_string(text, self.DEFAULT_MAX_LENGTH)
        )
    except excepts.Error as exc:
        raise excepts.ItemSaleError(exc)


sale.cmd = 0x80


def return_sale(self, item, department_num=0, tax1=0, tax2=0, tax3=0, tax4=0):
    """
    Возврат продажи.
    """

    text, quantity, price = item

    return self.protocol.command(
        0x82,
        self.password,
        misc.CAST_SIZE['11111'](*misc.int_to_bytes(quantity, 5)),
        misc.CAST_SIZE['11111'](*misc.int_to_bytes(price, 5)),
        misc.CAST_SIZE['1'](department_num),
        misc.CAST_SIZE['1111'](tax1, tax2, tax3, tax4),
        misc.prepare_string(text, self.DEFAULT_MAX_LENGTH)
    )


return_sale.cmd = 0x82


def close_check_ex(self, payments, discount_allowance=0, tax1=0, tax2=0, tax3=0, tax4=0, text=None):
    """
    payments - [0] - cash, [1:15] - payment_type[x]
    """

    payments += [0] * 16
    payments = payments[:16]
    payments_data = [
        misc.CAST_SIZE['11111'](*misc.int_to_bytes(p, 5)) for p in payments
    ]

    try:
        return self.protocol.command(
            0x8E,
            self.password,
            *payments_data,
            # TODO: проверить скидку/надбавку
            misc.CAST_SIZE['s2'](discount_allowance),
            misc.CAST_SIZE['1111'](tax1, tax2, tax3, tax4),
            misc.prepare_string(text, self.DEFAULT_MAX_LENGTH)
        )
    except excepts.ProtocolError as exc:
        raise excepts.CloseCheckError(exc)


close_check_ex.cmd = 0x8E


def close_check(self,
                cash=0,
                payment_type2=0,
                payment_type3=0,
                payment_type4=0,
                discount_allowance=0,
                tax1=0,
                tax2=0,
                tax3=0,
                tax4=0,
                text=None):
    """
    Закрытие чека.
    """

    try:
        return self.protocol.command(
            0x85,
            self.password,
            misc.CAST_SIZE['11111'](*misc.int_to_bytes(cash, 5)),
            misc.CAST_SIZE['11111'](*misc.int_to_bytes(payment_type2, 5)),
            misc.CAST_SIZE['11111'](*misc.int_to_bytes(payment_type3, 5)),
            misc.CAST_SIZE['11111'](*misc.int_to_bytes(payment_type4, 5)),
            # TODO: проверить скидку/надбавку
            misc.CAST_SIZE['s2'](discount_allowance),
            misc.CAST_SIZE['1111'](tax1, tax2, tax3, tax4),
            misc.prepare_string(text, self.DEFAULT_MAX_LENGTH)
        )
    except excepts.ProtocolError as exc:
        raise excepts.CloseCheckError(exc)


close_check.cmd = 0x85


def discount(self, sum_, tax1=0, tax2=0, tax3=0, tax4=0, text=None):
    """
    Скидка.
    """

    return self.protocol.command(
        0x86,
        self.password,
        misc.CAST_SIZE['11111'](*misc.int_to_bytes(sum_, 5)),
        misc.CAST_SIZE['1111'](tax1, tax2, tax3, tax4),
        misc.prepare_string(text, self.DEFAULT_MAX_LENGTH)
    )


discount.cmd = 0x86


def allowance(self, sum_, tax1=0, tax2=0, tax3=0, tax4=0, text=None):
    """
    Надбавка.
    """

    return self.protocol.command(
        0x87,
        self.password,
        misc.CAST_SIZE['11111'](*misc.int_to_bytes(sum_, 5)),
        misc.CAST_SIZE['1111'](tax1, tax2, tax3, tax4),
        misc.prepare_string(text, self.DEFAULT_MAX_LENGTH)
    )


allowance.cmd = 0x87


def cancel_check(self):
    """
    Аннулирование чека.
    """

    self.wait_printing()
    return self.protocol.command(
        0x88,
        self.password
    )


cancel_check.cmd = 0x88


def repeat(self):
    """
    Повтор документа.
    """

    self.wait_printing()
    return self.protocol.command(
        0x8C,
        self.password
    )


repeat.cmd = 0x8C


def open_check(self, check_type):
    """
    Открыть чек.
    #0 - продажа, 1 - покупка, 2 - возврат продажи, 3 - возврат покупки
    """

    self.wait_printing()
    try:
        return self.protocol.command(
            0x8D,
            self.password,
            misc.CAST_SIZE['1'](check_type)
        )
    except excepts.Error as exc:
        raise excepts.OpenCheckError(exc)


open_check.cmd = 0x8D


def continue_print(self):
    """
    Продолжение печати.
    """

    return self.protocol.command(
        0xB0,
        self.admin_password
    )


continue_print.cmd = 0xB0


def load_graphics(self, line_num, *args):
    """
    Загрузка графики.
    """

    return self.protocol.command(
        0xC0,
        self.password,
        misc.CAST_SIZE['1'](line_num),
        *args
    )


load_graphics.cmd = 0xC0


def print_graphics(self, start_line, end_line):
    """
    Печать графики.
    """

    self.wait_printing()
    return self.protocol.command(
        0xC1,
        self.password,
        misc.CAST_SIZE['1'](start_line),
        misc.CAST_SIZE['1'](end_line)
    )


print_graphics.cmd = 0xC1


def print_barcode(self, num):
    """
    Печать штрих-кода
    """

    self.wait_printing()
    return self.protocol.command(
        0xC2,
        self.password,
        misc.CAST_SIZE['11111'](*misc.int_to_bytes(num, 5))
    )


print_barcode.cmd = 0xC2


def open_shift(self):
    """
    Открыть смену.
    """

    return self.protocol.command(
        0xE0,
        self.password
    )


open_shift.cmd = 0xE0


def model(self):
    """
    Получить тип устройства.
    """

    return self.protocol.command_nopass(
        0xFC
    )


model.cmd = 0xFC


def fs_state(self):
    """
    Запрос статуса ФН.
    """

    return self.protocol.command(
        0xFF01,
        self.admin_password
    )


fs_state.cmd = 0xFF01


def fs_expiration_time(self):
    """
    Запрос срока действия ФН.
    """

    return self.protocol.command(
        0xFF03,
        self.admin_password
    )


fs_expiration_time.cmd = 0xFF03


def fs_cancel_document(self):
    """
    Отменить документ в ФН.
    """

    return self.protocol.command(
        0xFF08,
        self.admin_password
    )


fs_cancel_document.cmd = 0xFF08


def fs_find_document_by_num(self, num):
    """
    Найти фискальный документ по номеру.
    """

    return self.protocol.command(
        0xFF0A,
        self.admin_password,
        misc.CAST_SIZE['4'](num)
    )


fs_find_document_by_num.cmd = 0xFF0A


def fs_open_shift(self):
    """
    Открыть смену в ФН.
    """

    return self.protocol.command(
        0xFF0B,
        self.admin_password
    )


fs_open_shift.cmd = 0xFF0B


def send_tlv_struct(self, tlv_struct):
    """
    Передать произвольную TLV структуру.
    """

    if len(tlv_struct) > misc.TLV_LEN_MAX:
        raise ValueError(
            u'Максимальный размер tlv структуры - {} байт'.format(misc.TLV_LEN_MAX)
        )

    return self.protocol.command(
        0xFF0C,
        self.admin_password,
        tlv_struct
    )


send_tlv_struct.cmd = 0xFF0C


def send_tlv_struct_line(self, tlv_struct):
    """
    Передать произвольную TLV структуру.
    """

    if len(tlv_struct) > misc.TLV_LEN_MAX:
        raise ValueError(
            u'Максимальный размер tlv структуры - {} байт'.format(misc.TLV_LEN_MAX)
        )

    return self.protocol.command(
        0xFF4D,
        self.admin_password,
        tlv_struct
    )


send_tlv_struct_line.cmd = 0xFF4D


def fs_begin_correction_check(self):
    """
    Начать формирование чека коррекции.
    """

    return self.protocol.command(
        0xFF35,
        self.admin_password
    )


fs_begin_correction_check.cmd = 0xFF35


def fs_correction_check(self, sum_, check_type):
    """
    Сформировать чек коррекции.
    """

    return self.protocol.command(
        0xFF36,
        self.admin_password,
        misc.CAST_SIZE['11111'](*misc.int_to_bytes(sum_, 5)),
        misc.CAST_SIZE['1'](check_type)
    )


fs_correction_check.cmd = 0xFF36


def fs_calculation_state_report(self):
    """
    Сформировать отчёт о состоянии расчётов.
    """

    return self.protocol.command(
        0xFF38,
        self.admin_password
    )


fs_calculation_state_report.cmd = 0xFF38


def fs_info_exchange(self):
    """
    Получить статус информационного обмена.
    """

    return self.protocol.command(
        0xFF39,
        self.admin_password
    )


fs_info_exchange.cmd = 0xFF39


def fs_unconfirmed_document_count(self):
    """
    Запрос количества ФД на которые нет квитанции.
    """

    return self.protocol.command(
        0xFF3F,
        self.admin_password
    )


fs_unconfirmed_document_count.cmd = 0xFF3F


def fs_shift_params(self):
    """
    Запрос параметров текущей смены.
    """

    return self.protocol.command(
        0xFF40,
        self.admin_password
    )


fs_shift_params.cmd = 0xFF40


def fs_begin_open_shift(self):
    """
    Начать открытие смены.
    """

    return self.protocol.command(
        0xFF41,
        self.admin_password
    )


fs_begin_open_shift.cmd = 0xFF41


def fs_begin_close_shift(self):
    """
    Начать закрытие смены.
    """

    return self.protocol.command(
        0xFF42,
        self.admin_password
    )


fs_begin_close_shift.cmd = 0xFF42


def fs_close_shift(self):
    """
    Закрыть смену в ФН.
    """

    return self.protocol.command(
        0xFF43,
        self.admin_password
    )


fs_close_shift.cmd = 0xFF43


def operation_v2(self, oper_type, item, department_num=0, item_sum=0xffffffffff, tax_rate=0, tax_sum=0xFFFFFFFFFF,
                 method=1, subject=1):
    """
    oper_type - тип операции
        1 – Приход,
        2 – Возврат прихода,
        3 – Расход,
        4 – Возврат расхода
    tax_rate - тег tlv 1199 - ставка налога
        0x01 - НДС 20% (значение тега 1199: 1)
        0x02 - НДС 10% (значение тега 1199: 2)
        0x04 - НДС 0% (значение тега 1199: 5)
        0x08 - БЕЗ НДС (значение тега 1199: 6)
        0x10 - НДС 20/120 (значение тега 1199: 3)
        0x20 - НДС 10/110 (значение тега 1199: 4)
        0x81 - НДС 5% (значение тега 1199: 7)
        0x82 - НДС 7% (значение тега 1199: 8)
        0x84 - НДС 5/105 (значение тега 1199: 9)
        0x88 - НДС 7/107 (значение тега 1199: 10)
    tax_summ - сумма налогов
    subject - тег tlv 1212: наименование предмета расчета
        1 - товар
        2 - акциз товар
        3 - работа
        4 - услуга
    method - тег tlv 1214: признак способа расчета
        1 - предоплата 100%
        2 - предоплата
        3 - аванс
        4 - полный расчёт
        5 - частичный расчет и кредит
        6 - передача в кредит
        7 - оплата кредита
    """
    text, quantity, price = item

    return self.protocol.command(
        0xFF46,
        self.password,
        misc.CAST_SIZE['1'](oper_type),
        misc.CAST_SIZE['111111'](*misc.int_to_bytes(quantity, 6)),  # ???
        misc.CAST_SIZE['11111'](*misc.int_to_bytes(price, 5)),
        misc.CAST_SIZE['11111'](*misc.int_to_bytes(item_sum, 5)),
        misc.CAST_SIZE['11111'](*misc.int_to_bytes(tax_sum, 5)),
        misc.CAST_SIZE['1'](tax_rate),
        misc.CAST_SIZE['1'](department_num),
        misc.CAST_SIZE['1'](method),
        misc.CAST_SIZE['1'](subject),
        misc.prepare_string(text, self.DEFAULT_MAX_LENGTH)
    )


operation_v2.cmd = 0xFF46


def close_check_ex_v2(self, payments=None, round_kopecks=0, taxes=None, tax_system=0, text=None, add_taxes=None):
    """
    Закрытие чека расширенное в2.
    
    payments - список из 16 сумм типов оплаты:
        [0] - наличные
        [1-12] - тип оплаты 2-13 (безналичные)
        [13] - аванс
        [14] - кредит
        [15] - встречное представление
    
    round_kopecks - округление до рубля в копейках (1 байт)
    
    taxes - список из 6 сумм налогов:
        [0] - НДС 20%
        [1] - НДС 10%
        [2] - НДС 0%
        [3] - Без НДС
        [4] - НДС расч. 20/120
        [5] - НДС расч. 10/110
    
    tax_system - система налогообложения (1 байт):
        Бит 0 – ОСН
        Бит 1 – УСН доход
        Бит 2 – УСН доход минус расход
        Бит 3 – ЕНВД
        Бит 4 – ЕСП
        Бит 5 – ПСН
    
    text - текст (0-64 байт)
    
    add_taxes - список из 4 дополнительных налогов (опционально):
        [0] - НДС 5%
        [1] - НДС 7%
        [2] - НДС расч. 5/105
        [3] - НДС расч. 7/107
        
    Примечание:
    - Если add_taxes указан, то длина сообщения будет 202 байта, и текст должен быть дополнен нулями справа до длины 64 байта.
    - В режиме начисления налогов 0, 2 и 3 (1 Таблица) касса рассчитывает налоги самостоятельно, и налоги, переданные в команде, игнорируются.
    - В режиме начисления налогов 1 налоги должны быть обязательно переданы из верхнего ПО.
    """
    
    # Значения по умолчанию
    if payments is None:
        payments = [0] * 16
    else:
        payments = payments[:16] + [0] * (16 - len(payments))
    
    if taxes is None:
        taxes = [0] * 6
    else:
        taxes = taxes[:6] + [0] * (6 - len(taxes))
    
    # Преобразуем суммы оплат в байты
    payments_data = []
    for payment in payments:
        payments_data.append(misc.CAST_SIZE['11111'](*misc.int_to_bytes(payment, 5)))
    
    # Преобразуем налоги в байты
    taxes_data = []
    for tax in taxes:
        taxes_data.append(misc.CAST_SIZE['11111'](*misc.int_to_bytes(tax, 5)))
    
    # Базовые параметры команды
    command_params = []
    command_params.extend(payments_data)
    command_params.append(misc.CAST_SIZE['1'](round_kopecks))
    command_params.extend(taxes_data)
    command_params.append(misc.CAST_SIZE['1'](tax_system))
    
    # Если указаны дополнительные налоги, добавляем их и дополняем текст до 64 байт
    if add_taxes is not None:
        if len(add_taxes) < 4:
            add_taxes = add_taxes + [0] * (4 - len(add_taxes))
        
        # Подготавливаем текст (дополняем нулями до 64 байт)
        if text is None:
            text = ""
        prepared_text = misc.prepare_string(text, 64)
        
        # Добавляем текст и дополнительные налоги
        command_params.append(prepared_text)
        
        # Добавляем дополнительные налоги
        for tax in add_taxes:
            command_params.append(misc.CAST_SIZE['11111'](*misc.int_to_bytes(tax, 5)))
    else:
        # Если дополнительных налогов нет, просто добавляем текст
        if text is not None:
            command_params.append(misc.prepare_string(text, self.DEFAULT_MAX_LENGTH))
        else:
            command_params.append(bytearray())
    
    try:
        return self.protocol.command(
            0xFF45,
            self.password,
            *command_params
        )
    except excepts.ProtocolError as exc:
        raise excepts.CloseCheckError(exc)


close_check_ex_v2.cmd = 0xFF45


def close_shift_buffer(self):
    """
    Закрыть смену в буфер.
    """

    return self.protocol.command(
        0xC6,
        self.admin_password
    )


close_shift_buffer.cmd = 0xC6


def print_buffer(self):
    """
    Распечатать отчет из буфера.
    """

    return self.protocol.command(
        0xC7,
        self.admin_password
    )


print_buffer.cmd = 0xC7


def wait_printing(self):
    """
    Метод ожидания окончания печати документа.
    """

    while True:
        time.sleep(self.WAIT_TIME)

        state_ = self.state()
        mode = state_[u'Режим ФР']
        submode = state_[u'Подрежим ФР']

        if mode.num == 12:
            continue

        if submode.state == 0:
            return
        if submode.state == 3:
            self.continue_print()


print_string.depends = (wait_printing,)
print_font.depends = (wait_printing,)
test_start.depends = (wait_printing,)
cut.depends = (wait_printing,)
feed.depends = (wait_printing,)
test_stop.depends = (wait_printing,)
x_report.depends = (wait_printing,)
z_report.depends = (wait_printing,)
sections_report.depends = (wait_printing,)
income.depends = (wait_printing,)
outcome.depends = (wait_printing,)
cancel_check.depends = (wait_printing,)
repeat.depends = (wait_printing,)
open_check.depends = (wait_printing,)
print_graphics.depends = (wait_printing,)
print_barcode.depends = (wait_printing,)

module_ = sys.modules[__name__]
FUNCTIONS = {
    function_.cmd if hasattr(function_, 'cmd') else name: function_
    for name, function_ in inspect.getmembers(module_, inspect.isfunction)
    if function_.__module__ == module_.__name__
}


class SupportedCommands(type):
    def __new__(mcs, classname, supers, attributedict):
        command_nums = attributedict.get('SUPPORTED_COMMANDS', ())

        def relative_gen(cmd):
            if hasattr(cmd, 'depends'):
                for dpc in cmd.depends:
                    relative_gen(dpc)
                    if dpc not in attributedict.values():
                        yield dpc

            if hasattr(cmd, 'required'):
                if all(rqc in attributedict.values() for rqc in cmd.required):
                    yield cmd

            if hasattr(cmd, 'related'):
                for rlc in cmd.related:
                    relative_gen(rlc)
                    if rlc not in attributedict.values():
                        yield rlc

        for cn in command_nums:
            command = FUNCTIONS[cn]
            attributedict[command.__name__] = command

            for c in relative_gen(command):
                attributedict[c.__name__] = c

        return super(SupportedCommands, mcs).__new__(mcs, classname, supers, attributedict)
