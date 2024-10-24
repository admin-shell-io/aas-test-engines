from decimal import Decimal, DecimalException
from typing import Pattern, Dict, Mapping
import re
import base64


def is_decimal(s: str) -> bool:
    try:
        Decimal(s)
        return True
    except DecimalException:
        return False


def _is_bounded_double(s: str, min: float, max: float) -> bool:
    if s in ['INF', '-INF', 'NaN']:
        return True
    try:
        v = float(s)
        return v > min and v < max
    except ValueError:
        return False


def is_float(s: str) -> bool:
    return _is_bounded_double(s, -3.4028234663852886e+38, 3.4028234663852886e+38)


def is_double(s: str) -> bool:
    return _is_bounded_double(s, -1.7976931348623158e+308, 1.7976931348623158e+308)


def _is_bounded_integer(s: int, min: int, max: int) -> bool:
    try:
        v = int(s)
        return v >= min and v <= max
    except ValueError:
        return False


def is_hex_binary(s: str) -> bool:
    try:
        bytes.fromhex(s)
        return True
    except KeyError:
        return False


def _is_leap_year(year: int) -> bool:
    if year < 0:
        year = abs(year) - 1
    if year % 4 > 0:
        return False
    if year % 100 > 0:
        return True
    if year % 400 > 0:
        return False
    return True


_DAYS_IN_MONTH: Mapping[int, int] = {
    1: 31,
    # Please use _is_leap_year if you need to check
    # whether a concrete February has 28 or 29 days.
    2: 29,
    3: 31,
    4: 30,
    5: 31,
    6: 30,
    7: 31,
    8: 31,
    9: 30,
    10: 31,
    11: 30,
    12: 31,
}


def _construct_matches_xs_date() -> Pattern[str]:
    digit = "[0-9]"
    year_frag = f"-?(([1-9]{digit}{digit}{digit}+)|(0{digit}{digit}{digit}))"
    month_frag = "((0[1-9])|(1[0-2]))"
    day_frag = f"((0[1-9])|([12]{digit})|(3[01]))"
    minute_frag = f"[0-5]{digit}"
    timezone_frag = f"(Z|(\\+|-)((0{digit}|1[0-3]):{minute_frag}|14:00))"
    date_lexical_rep = f"{year_frag}-{month_frag}-{day_frag}{timezone_frag}?"
    pattern = f"^{date_lexical_rep}$"

    return re.compile(pattern)


_REGEX_MATCHES_XS_DATE = _construct_matches_xs_date()

_DATE_PREFIX_RE = re.compile(r"^(-?[0-9]+)-([0-9]{2})-([0-9]{2})")


def is_xs_date(value: str) -> bool:
    if _REGEX_MATCHES_XS_DATE.match(value) is None:
        return False

    match = _DATE_PREFIX_RE.match(value)
    assert match is not None

    year = int(match.group(1))
    month = int(match.group(2))
    day = int(match.group(3))

    if year == 0:
        return False
    if day <= 0:
        return False
    if month <= 0 or month >= 13:
        return False

    if month == 2:
        max_days = 29 if _is_leap_year(year) else 28
    else:
        max_days = _DAYS_IN_MONTH[month]

    if day > max_days:
        return False

    return True


def _construct_matches_xs_date_time() -> Pattern[str]:
    digit = "[0-9]"
    year_frag = f"-?(([1-9]{digit}{digit}{digit}+)|(0{digit}{digit}{digit}))"
    month_frag = "((0[1-9])|(1[0-2]))"
    day_frag = f"((0[1-9])|([12]{digit})|(3[01]))"
    hour_frag = f"(([01]{digit})|(2[0-3]))"
    minute_frag = f"[0-5]{digit}"
    second_frag = f"([0-5]{digit})(\\.{digit}+)?"
    end_of_day_frag = "24:00:00(\\.0+)?"
    timezone_frag = f"(Z|(\\+|-)((0{digit}|1[0-3]):{minute_frag}|14:00))"
    date_time_lexical_rep = f"{year_frag}-{month_frag}-{day_frag}T(({hour_frag}:{minute_frag}:{second_frag})|{end_of_day_frag}){timezone_frag}?"
    pattern = f"^{date_time_lexical_rep}$"

    return re.compile(pattern)


_REGEX_MATCHES_XS_DATE_TIME = _construct_matches_xs_date_time()


def is_xs_date_time(s: str) -> bool:
    if _REGEX_MATCHES_XS_DATE_TIME.match(s) is None:
        return False

    date, _ = s.split("T")
    return is_xs_date(date)


def _construct_matches_xs_date_time_utc() -> Pattern[str]:
    digit = "[0-9]"
    year_frag = f"-?(([1-9]{digit}{digit}{digit}+)|(0{digit}{digit}{digit}))"
    month_frag = "((0[1-9])|(1[0-2]))"
    day_frag = f"((0[1-9])|([12]{digit})|(3[01]))"
    hour_frag = f"(([01]{digit})|(2[0-3]))"
    minute_frag = f"[0-5]{digit}"
    second_frag = f"([0-5]{digit})(\\.{digit}+)?"
    end_of_day_frag = "24:00:00(\\.0+)?"
    timezone_frag = "(Z|\\+00:00|-00:00)"
    date_time_lexical_rep = f"{year_frag}-{month_frag}-{day_frag}T(({hour_frag}:{minute_frag}:{second_frag})|{end_of_day_frag}){timezone_frag}"
    pattern = f"^{date_time_lexical_rep}$"

    return re.compile(pattern)


_REGEX_MATCHES_XS_DATE_TIME_UTC = _construct_matches_xs_date_time_utc()


def is_xs_date_time_utc(s: str) -> bool:
    if _REGEX_MATCHES_XS_DATE_TIME_UTC.match(s) is None:
        return False

    date, _ = s.split("T")
    return is_xs_date(date)


_DAYS_IN_MONTH: Dict[int, int] = {
    1: 31,
    2: 29,
    3: 31,
    4: 30,
    5: 31,
    6: 30,
    7: 31,
    8: 31,
    9: 30,
    10: 31,
    11: 30,
    12: 31,
}


def _days_in_month(month: int, year: int) -> int:
    if month == 2:
        return 29 if _is_leap_year(year) else 28
    else:
        return _DAYS_IN_MONTH[month]


def _construct_matches_xs_any_uri() -> Pattern[str]:
    scheme = "[a-zA-Z][a-zA-Z0-9+\\-.]*"
    ucschar = "[\\xa0-\\ud7ff\\uf900-\\ufdcf\\ufdf0-\\uffef\\U00010000-\\U0001fffd\\U00020000-\\U0002fffd\\U00030000-\\U0003fffd\\U00040000-\\U0004fffd\\U00050000-\\U0005fffd\\U00060000-\\U0006fffd\\U00070000-\\U0007fffd\\U00080000-\\U0008fffd\\U00090000-\\U0009fffd\\U000a0000-\\U000afffd\\U000b0000-\\U000bfffd\\U000c0000-\\U000cfffd\\U000d0000-\\U000dfffd\\U000e1000-\\U000efffd]"
    iunreserved = f"([a-zA-Z0-9\\-._~]|{ucschar})"
    pct_encoded = "%[0-9A-Fa-f][0-9A-Fa-f]"
    sub_delims = "[!$&'()*+,;=]"
    iuserinfo = f"({iunreserved}|{pct_encoded}|{sub_delims}|:)*"
    h16 = "[0-9A-Fa-f]{1,4}"
    dec_octet = "([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])"
    ipv4address = f"{dec_octet}\\.{dec_octet}\\.{dec_octet}\\.{dec_octet}"
    ls32 = f"({h16}:{h16}|{ipv4address})"
    ipv6address = f"(({h16}:){{6}}{ls32}|::({h16}:){{5}}{ls32}|({h16})?::({h16}:){{4}}{ls32}|(({h16}:)?{h16})?::({h16}:){{3}}{ls32}|(({h16}:){{2}}{h16})?::({h16}:){{2}}{ls32}|(({h16}:){{3}}{h16})?::{h16}:{ls32}|(({h16}:){{4}}{h16})?::{ls32}|(({h16}:){{5}}{h16})?::{h16}|(({h16}:){{6}}{h16})?::)"
    unreserved = "[a-zA-Z0-9\\-._~]"
    ipvfuture = f"[vV][0-9A-Fa-f]+\\.({unreserved}|{sub_delims}|:)+"
    ip_literal = f"\\[({ipv6address}|{ipvfuture})\\]"
    ireg_name = f"({iunreserved}|{pct_encoded}|{sub_delims})*"
    ihost = f"({ip_literal}|{ipv4address}|{ireg_name})"
    port = "[0-9]*"
    iauthority = f"({iuserinfo}@)?{ihost}(:{port})?"
    ipchar = f"({iunreserved}|{pct_encoded}|{sub_delims}|[:@])"
    isegment = f"({ipchar})*"
    ipath_abempty = f"(/{isegment})*"
    isegment_nz = f"({ipchar})+"
    ipath_absolute = f"/({isegment_nz}(/{isegment})*)?"
    ipath_rootless = f"{isegment_nz}(/{isegment})*"
    ipath_empty = f"({ipchar}){{0}}"
    ihier_part = f"(//{iauthority}{ipath_abempty}|{ipath_absolute}|{ipath_rootless}|{ipath_empty})"
    iprivate = "[\\ue000-\\uf8ff\\U000f0000-\\U000ffffd\\U00100000-\\U0010fffd]"
    iquery = f"({ipchar}|{iprivate}|[/?])*"
    ifragment = f"({ipchar}|[/?])*"
    isegment_nz_nc = f"({iunreserved}|{pct_encoded}|{sub_delims}|@)+"
    ipath_noscheme = f"{isegment_nz_nc}(/{isegment})*"
    irelative_part = f"(//{iauthority}{ipath_abempty}|{ipath_absolute}|{ipath_noscheme}|{ipath_empty})"
    irelative_ref = f"{irelative_part}(\\?{iquery})?(#{ifragment})?"
    iri = f"{scheme}:{ihier_part}(\\?{iquery})?(#{ifragment})?"
    iri_reference = f"({iri}|{irelative_ref})"
    pattern = f"^{iri_reference}$"

    return re.compile(pattern)


def _construct_matches_xs_g_month_day() -> Pattern[str]:
    g_month_day_rep = "--(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])(Z|(\\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?"
    pattern = f"^{g_month_day_rep}$"

    return re.compile(pattern)


_REGEX_MATCHES_XS_G_MONTH_DAY = _construct_matches_xs_g_month_day()


def is_xs_g_month_day(s: str) -> bool:
    if _REGEX_MATCHES_XS_G_MONTH_DAY.match(s) is None:
        return False
    month = int(s[2:4])
    day = int(s[5:7])

    max_days = _DAYS_IN_MONTH[month]
    return day <= max_days


_REGEX_MATCHES_XS_ANY_URI = _construct_matches_xs_any_uri()


def is_any_uri(s: str) -> bool:
    return _REGEX_MATCHES_XS_ANY_URI.match(s) is not None


def is_base64_binary(s: str) -> bool:
    try:
        base64.b64decode(s)
        return True
    except ValueError:
        return False


def _construct_matches_bcp_47() -> Pattern[str]:
    alphanum = '[a-zA-Z0-9]'
    singleton = '[0-9A-WY-Za-wy-z]'
    extension = f'{singleton}(-({alphanum}){{2,8}})+'
    extlang = '[a-zA-Z]{3}(-[a-zA-Z]{3}){0,2}'
    irregular = '(en-GB-oed|i-ami|i-bnn|i-default|i-enochian|i-hak|i-klingon|i-lux|i-mingo|i-navajo|i-pwn|i-tao|i-tay|i-tsu|sgn-BE-FR|sgn-BE-NL|sgn-CH-DE)'
    regular = '(art-lojban|cel-gaulish|no-bok|no-nyn|zh-guoyu|zh-hakka|zh-min|zh-min-nan|zh-xiang)'
    grandfathered = f'({irregular}|{regular})'
    language = f'([a-zA-Z]{{2,3}}(-{extlang})?|[a-zA-Z]{{4}}|[a-zA-Z]{{5,8}})'
    script = '[a-zA-Z]{4}'
    region = '([a-zA-Z]{2}|[0-9]{3})'
    variant = f'(({alphanum}){{5,8}}|[0-9]({alphanum}){{3}})'
    privateuse = f'[xX](-({alphanum}){{1,8}})+'
    langtag = f'{language}(-{script})?(-{region})?(-{variant})*(-{extension})*(-{privateuse})?'
    language_tag = f'({langtag}|{privateuse}|{grandfathered})'
    pattern = f'^{language_tag}$'

    return re.compile(pattern)


_REGEX_MATCHES_BCP_47 = _construct_matches_bcp_47()


def is_bcp_lang_string(s: str) -> bool:
    return _REGEX_MATCHES_BCP_47.match(s) is not None


def _construct_matches_version_type() -> Pattern[str]:
    pattern = '^(0|[1-9][0-9]*)$'
    return re.compile(pattern)


_REGEX_MATCHES_VERSION_TYPE = _construct_matches_version_type()


def is_version_string(text: str) -> bool:
    return _REGEX_MATCHES_VERSION_TYPE.match(text) is not None


_REGEX_IS_BCP_47_FOR_ENGLISH = re.compile("^(en|EN)(-.*)?$")


def is_bcp_47_for_english(text: str) -> bool:
    return _REGEX_IS_BCP_47_FOR_ENGLISH.match(text) is not None


validators = {
    'xs:decimal': is_decimal,
    'xs:integer': lambda s: _is_bounded_integer(s, float('-inf'), float('inf')),

    'xs:float': is_float,
    'xs:double': is_double,

    'xs:byte': lambda s: _is_bounded_integer(s, -128, 127),
    'xs:short': lambda s: _is_bounded_integer(s, -32768, 32767),
    'xs:int': lambda s: _is_bounded_integer(s, -2147483648, 2147483647),
    'xs:long': lambda s: _is_bounded_integer(s, -9223372036854775808, 9223372036854775807),

    'xs:unsignedByte': lambda s: _is_bounded_integer(s, 0, 255),
    'xs:unsignedShort': lambda s: _is_bounded_integer(s, 0, 65535),
    'xs:unsignedInt': lambda s: _is_bounded_integer(s, 0, 4294967295),
    'xs:unsignedLong': lambda s: _is_bounded_integer(s, 0, 18446744073709551615),

    'xs:positiveInteger': lambda s: _is_bounded_integer(s, 1, float('inf')),
    'xs:nonNegativeInteger': lambda s: _is_bounded_integer(s, 0, float('inf')),
    'xs:negativeInteger': lambda s: _is_bounded_integer(s, float('-inf'), -1),
    'xs:nonPositiveInteger': lambda s: _is_bounded_integer(s, float('-inf'), 0),

    'xs:date': is_xs_date,
    'xs:dateTime': is_xs_date_time,
    'xs:gMonthDay': is_xs_g_month_day,
    'xs:dateTimeUTC': is_xs_date_time_utc,
    'xs:gYearMonth': lambda x: True,
    'xs:gDay': lambda x: True,
    'xs:gMonth': lambda x: True,
    'xs:gYear': lambda x: True,
    'xs:time': lambda x: True,
    'xs:duration': lambda x: True,

    'xs:anyURI': is_any_uri,
    'xs:base64Binary': is_base64_binary,

    'bcpLangString': is_bcp_lang_string,
    'version': is_version_string,
    'contentType': lambda x: True,
    'path': lambda x: True,
}
