package com.vpet.mobile

/**
 * 轻量 JSON object（仅 object / 标量 / 嵌套 object），供 commonMain 存档。
 */
class SimpleJson(private val map: MutableMap<String, Any?> = linkedMapOf()) {
    fun put(key: String, value: Any?): SimpleJson {
        map[key] = value
        return this
    }

    fun has(key: String): Boolean = map.containsKey(key)
    fun remove(key: String) {
        map.remove(key)
    }

    fun optString(key: String, default: String = ""): String {
        val v = map[key] ?: return default
        return v.toString()
    }

    fun optInt(key: String, default: Int = 0): Int = when (val v = map[key]) {
        is Int -> v
        is Long -> v.toInt()
        is Double -> v.toInt()
        is String -> v.toIntOrNull() ?: default
        else -> default
    }

    fun optLong(key: String, default: Long = 0L): Long = when (val v = map[key]) {
        is Long -> v
        is Int -> v.toLong()
        is Double -> v.toLong()
        is String -> v.toLongOrNull() ?: default
        else -> default
    }

    fun optDouble(key: String, default: Double = 0.0): Double = when (val v = map[key]) {
        is Double -> v
        is Float -> v.toDouble()
        is Int -> v.toDouble()
        is Long -> v.toDouble()
        is String -> v.toDoubleOrNull() ?: default
        else -> default
    }

    fun optBoolean(key: String, default: Boolean = false): Boolean = when (val v = map[key]) {
        is Boolean -> v
        is String -> v.equals("true", ignoreCase = true)
        else -> default
    }

    fun optObject(key: String): SimpleJson? = when (val v = map[key]) {
        is SimpleJson -> v
        is Map<*, *> -> {
            val o = SimpleJson()
            v.forEach { (k, value) -> if (k != null) o.put(k.toString(), value) }
            o
        }
        else -> null
    }

    fun ensureObject(key: String): SimpleJson {
        val existing = optObject(key)
        if (existing != null) return existing
        val created = SimpleJson()
        put(key, created)
        return created
    }

    fun keys(): Set<String> = map.keys.toSet()

    fun encode(pretty: Boolean = false): String = encodeMap(map, pretty, 0)

    companion object {
        fun parse(raw: String?): SimpleJson {
            if (raw.isNullOrBlank()) return SimpleJson()
            return try {
                val p = Parser(raw.trim())
                p.parseValue() as? SimpleJson ?: SimpleJson()
            } catch (_: Exception) {
                SimpleJson()
            }
        }

        fun of(vararg pairs: Pair<String, Any?>): SimpleJson =
            SimpleJson(linkedMapOf(*pairs))

        private fun encodeMap(m: Map<*, *>, pretty: Boolean, indent: Int): String {
            val nl = if (pretty) "\n" else ""
            val pad = if (pretty) " ".repeat(indent) else ""
            val pad2 = if (pretty) " ".repeat(indent + 2) else ""
            if (m.isEmpty()) return "{}"
            val body = m.entries.joinToString(",") { (k, v) ->
                "$nl$pad2\"${esc(k.toString())}\":${encodeAny(v, pretty, indent + 2)}"
            }
            return "{$body$nl$pad}"
        }

        private fun encodeAny(v: Any?, pretty: Boolean, indent: Int): String = when (v) {
            null -> "null"
            is String -> "\"${esc(v)}\""
            is Number, is Boolean -> v.toString()
            is SimpleJson -> encodeMap(v.map, pretty, indent)
            is Map<*, *> -> encodeMap(v, pretty, indent)
            is List<*> -> {
                val nl = if (pretty) "\n" else ""
                val pad = if (pretty) " ".repeat(indent) else ""
                val pad2 = if (pretty) " ".repeat(indent + 2) else ""
                if (v.isEmpty()) "[]"
                else "[${v.joinToString(",") { "$nl$pad2${encodeAny(it, pretty, indent + 2)}" }}$nl$pad]"
            }
            else -> "\"${esc(v.toString())}\""
        }

        private fun esc(s: String): String = buildString {
            for (c in s) when (c) {
                '\\' -> append("\\\\")
                '"' -> append("\\\"")
                '\n' -> append("\\n")
                '\r' -> append("\\r")
                '\t' -> append("\\t")
                else -> append(c)
            }
        }

        private class Parser(private val s: String) {
            private var i = 0

            fun parseValue(): Any? {
                skip()
                if (i >= s.length) error("eof")
                return when (s[i]) {
                    '{' -> parseObject()
                    '[' -> parseArray()
                    '"' -> parseString()
                    't' -> {
                        require(s.startsWith("true", i)); i += 4; true
                    }
                    'f' -> {
                        require(s.startsWith("false", i)); i += 5; false
                    }
                    'n' -> {
                        require(s.startsWith("null", i)); i += 4; null
                    }
                    else -> parseNumber()
                }
            }

            private fun parseObject(): SimpleJson {
                expect('{')
                val o = SimpleJson()
                skip()
                if (peek('}')) {
                    i++; return o
                }
                while (true) {
                    val key = parseString()
                    expect(':')
                    o.put(key, parseValue())
                    skip()
                    when {
                        peek(',') -> {
                            i++; continue
                        }
                        peek('}') -> {
                            i++; return o
                        }
                        else -> error("bad object at $i")
                    }
                }
            }

            private fun parseArray(): List<Any?> {
                expect('[')
                val list = mutableListOf<Any?>()
                skip()
                if (peek(']')) {
                    i++; return list
                }
                while (true) {
                    list += parseValue()
                    skip()
                    when {
                        peek(',') -> {
                            i++; continue
                        }
                        peek(']') -> {
                            i++; return list
                        }
                        else -> error("bad array at $i")
                    }
                }
            }

            private fun parseString(): String {
                expect('"')
                val sb = StringBuilder()
                while (i < s.length) {
                    when (val c = s[i++]) {
                        '"' -> return sb.toString()
                        '\\' -> {
                            when (val e = s[i++]) {
                                '"', '\\', '/' -> sb.append(e)
                                'n' -> sb.append('\n')
                                'r' -> sb.append('\r')
                                't' -> sb.append('\t')
                                'u' -> {
                                    val hex = s.substring(i, (i + 4).coerceAtMost(s.length))
                                    i += hex.length
                                    sb.append(hex.toIntOrNull(16)?.toChar() ?: '?')
                                }
                                else -> sb.append(e)
                            }
                        }
                        else -> sb.append(c)
                    }
                }
                error("unterminated string")
            }

            private fun parseNumber(): Number {
                val start = i
                if (peek('-')) i++
                while (i < s.length && s[i].isDigit()) i++
                var isDouble = false
                if (peek('.')) {
                    isDouble = true
                    i++
                    while (i < s.length && s[i].isDigit()) i++
                }
                if (i < s.length && (s[i] == 'e' || s[i] == 'E')) {
                    isDouble = true
                    i++
                    if (peek('+') || peek('-')) i++
                    while (i < s.length && s[i].isDigit()) i++
                }
                val raw = s.substring(start, i)
                return if (isDouble) raw.toDouble()
                else raw.toLong().let { if (it in Int.MIN_VALUE..Int.MAX_VALUE) it.toInt() else it }
            }

            private fun skip() {
                while (i < s.length && s[i].isWhitespace()) i++
            }

            private fun peek(c: Char): Boolean = i < s.length && s[i] == c

            private fun expect(c: Char) {
                skip()
                if (!peek(c)) error("expect $c at $i")
                i++
            }
        }
    }
}
