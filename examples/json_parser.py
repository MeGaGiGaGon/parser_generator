from parser_generator import *

ws = choose(
    any_of(" \r\n\t").then(ForwardRefParser(lambda: ws)).map("".join),
    empty().to(""),
)

string_rest = choose(just_seq('"').to(""), any_item().then(ForwardRefParser(lambda: string_rest)).map("".join))
string = just('"').ignore_then(string_rest)

object_member: Parser[str, tuple[str, str], Literal[True]] = string.then_ignore(ws).then_ignore(just(":")).then(ForwardRefParser(lambda: element))
object_members: Parser[str, list[tuple[str, str]], Literal[True]] = object_member.then(
    choose(just(",").then(ws).ignore_then(ForwardRefParser(lambda: object_members)), just("}").map(lambda _: {}))
).map(lambda x: {x[0][0]: x[0][1], **x[1]})

json_object = (
    just("{").then(ws).ignore_then(choose(just("}").map(lambda _: {}), empty().ignore_then(object_members)))
)

list_member = ws.ignore_then(ForwardRefParser(lambda: element))
list_members = list_member.then(choose(just(",").then(ws).ignore_then(ForwardRefParser(lambda: list_members)), just("]").map(lambda _: []))).map(lambda x: [x[0], *x[1]])
json_list = just("[").then(ws).ignore_then(choose(just("]").map(lambda _: []), empty().ignore_then(list_members)))

number_rest = choose(any_of("0123456789").then(ForwardRefParser(lambda: number_rest)).map("".join), empty().to(""))
number = choose(just("0"), any_of("123456789").then(number_rest).map("".join)).map(int)

element = ws.ignore_then(choose(json_object, json_list, string, number)).then_ignore(ws)

print(element('{ \n\r\t "}"  :   {}, "a": {"b": [1, [{"a":[0, 1,2,3,4,100]}]]   }}', 0))
