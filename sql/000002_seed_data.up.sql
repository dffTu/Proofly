-- Аксиомы (level = 0)
INSERT INTO graph_node (slug, title, node_type, level, description) VALUES
(
  'axiom-closure-add',
  'Замкнутость относительно сложения',
  'axiom', 0,
  E'## Аксиома: Замкнутость относительно сложения\n\nДля любых $a, b \\in \\mathbb{F}$:\n\n$$a + b \\in \\mathbb{F}$$\n\nЭто означает, что сложение двух элементов поля всегда даёт элемент того же поля. Данное свойство является **аксиомой** — оно принимается без доказательства как основа всей алгебраической системы.'
),
(
  'axiom-commutativity-add',
  'Коммутативность сложения',
  'axiom', 0,
  E'## Аксиома: Коммутативность сложения\n\nДля любых $a, b \\in \\mathbb{F}$:\n\n$$a + b = b + a$$\n\nПорядок слагаемых не влияет на результат. Это свойство — одна из основных аксиом поля, принимаемых без доказательства.'
),
(
  'axiom-associativity-add',
  'Ассоциативность сложения',
  'axiom', 0,
  E'## Аксиома: Ассоциативность сложения\n\nДля любых $a, b, c \\in \\mathbb{F}$:\n\n$$(a + b) + c = a + (b + c)$$\n\nПри сложении нескольких чисел результат не зависит от расстановки скобок. Данная аксиома позволяет нам писать $a + b + c$ без скобок.'
),
(
  'axiom-additive-identity',
  'Существование нуля',
  'axiom', 0,
  E'## Аксиома: Существование нейтрального элемента (нуля)\n\nСуществует элемент $0 \\in \\mathbb{F}$ такой, что для любого $a \\in \\mathbb{F}$:\n\n$$a + 0 = a$$\n\nЭлемент $0$ называется **нейтральным элементом** (нулём) по сложению. Аксиома постулирует его существование, но не единственность — единственность будет **доказана** как теорема ([Единственность нуля](#thm-unique-zero)).'
),
(
  'axiom-additive-inverse',
  'Существование противоположного элемента',
  'axiom', 0,
  E'## Аксиома: Существование противоположного элемента\n\nДля любого $a \\in \\mathbb{F}$ существует элемент $(-a) \\in \\mathbb{F}$ такой, что:\n\n$$a + (-a) = 0$$\n\nЭлемент $(-a)$ называется **противоположным** к $a$. Аксиома гарантирует его существование. Единственность будет доказана ([Единственность противоположного элемента](#thm-unique-inverse)).'
),
(
  'axiom-distributivity',
  'Дистрибутивность',
  'axiom', 0,
  E'## Аксиома: Дистрибутивность умножения относительно сложения\n\nДля любых $a, b, c \\in \\mathbb{F}$:\n\n$$a \\cdot (b + c) = a \\cdot b + a \\cdot c$$\n\nЭта аксиома связывает операции сложения и умножения, позволяя «раскрывать скобки». Из неё будут выведены многие важные свойства, в том числе [произведение на ноль](#thm-zero-product).'
)
ON CONFLICT (slug) DO NOTHING;

-- Теоремы уровня 1
INSERT INTO graph_node (slug, title, node_type, level, description) VALUES
(
  'thm-unique-zero',
  'Единственность нуля',
  'theorem', 1,
  E'## Теорема: Нейтральный элемент по сложению единственен\n\n**Утверждение:** В поле $\\mathbb{F}$ существует ровно один нейтральный элемент по сложению.\n\n**Доказательство:**\n\nПредположим, что существуют два нуля: $0$ и $0\'$, то есть:\n$$a + 0 = a \\quad \\text{и} \\quad a + 0\' = a \\quad \\text{для всех } a$$\n\nПоложим $a = 0\'$ в первом равенстве: $0\' + 0 = 0\'$.\nПоложим $a = 0$ во втором равенстве: $0 + 0\' = 0$.\n\nПо [аксиоме коммутативности](#axiom-commutativity-add): $0\' + 0 = 0 + 0\'$, значит:\n$$0\' = 0 \\quad \\blacksquare$$\n\n**Использованные аксиомы:** [существование нуля](#axiom-additive-identity), [коммутативность](#axiom-commutativity-add), [ассоциативность](#axiom-associativity-add).'
),
(
  'thm-unique-inverse',
  'Единственность противоположного элемента',
  'theorem', 1,
  E'## Теорема: Противоположный элемент единственен\n\n**Утверждение:** Для каждого $a \\in \\mathbb{F}$ противоположный элемент $(-a)$ единственен.\n\n**Доказательство:**\n\nПусть $b$ и $c$ — оба противоположны к $a$:\n$$a + b = 0 \\quad \\text{и} \\quad a + c = 0$$\n\nРассмотрим:\n$$b = b + 0 = b + (a + c) = (b + a) + c = 0 + c = c$$\n\nЗдесь использовались:\n- [Существование нуля](#axiom-additive-identity): $b + 0 = b$\n- Подстановку $0 = a + c$\n- [Ассоциативность](#axiom-associativity-add)\n- [Существование противоположного](#axiom-additive-inverse): $b + a = 0$\n\nСледовательно, $b = c$. $\\blacksquare$'
),
(
  'thm-cancellation',
  'Закон сокращения',
  'theorem', 1,
  E'## Теорема: Закон сокращения по сложению\n\n**Утверждение:** Если $a + b = a + c$, то $b = c$.\n\n**Доказательство:**\n\nДано: $a + b = a + c$. По [аксиоме существования противоположного](#axiom-additive-inverse) к $a$ существует $(-a)$. Прибавим $(-a)$ слева:\n\n$$(-a) + (a + b) = (-a) + (a + c)$$\n\nПо [ассоциативности](#axiom-associativity-add):\n$$((-a) + a) + b = ((-a) + a) + c$$\n$$0 + b = 0 + c$$\n\nПо [нейтральности нуля](#axiom-additive-identity) и [коммутативности](#axiom-commutativity-add):\n$$b = c \\quad \\blacksquare$$'
)
ON CONFLICT (slug) DO NOTHING;

-- Теоремы уровня 2
INSERT INTO graph_node (slug, title, node_type, level, description) VALUES
(
  'thm-double-negation',
  'Двойное отрицание: $-(-a) = a$',
  'theorem', 2,
  E'## Теорема: Двойное отрицание\n\n**Утверждение:** Для любого $a \\in \\mathbb{F}$: $-(-a) = a$.\n\n**Доказательство:**\n\nПо определению $(-a)$ — противоположный к $a$:\n$$a + (-a) = 0$$\n\nЗначит, $a$ является противоположным к $(-a)$. По теореме о [единственности противоположного элемента](#thm-unique-inverse):\n$$-(-a) = a \\quad \\blacksquare$$\n\n**Использованные результаты:** [существование противоположного](#axiom-additive-inverse), [единственность противоположного](#thm-unique-inverse).'
),
(
  'thm-zero-product',
  E'Произведение на ноль: $0 \\cdot a = 0$',
  'theorem', 2,
  E'## Теорема: Произведение любого элемента на ноль равно нулю\n\n**Утверждение:** Для любого $a \\in \\mathbb{F}$: $0 \\cdot a = 0$.\n\n**Доказательство:**\n\n$$0 \\cdot a = (0 + 0) \\cdot a$$\n\nПо [дистрибутивности](#axiom-distributivity):\n$$(0 + 0) \\cdot a = 0 \\cdot a + 0 \\cdot a$$\n\nОбозначим $x = 0 \\cdot a$. Тогда $x = x + x$. По [закону сокращения](#thm-cancellation):\n$$0 = x$$\n\n**Использованные результаты:** [существование нуля](#axiom-additive-identity), [дистрибутивность](#axiom-distributivity), [закон сокращения](#thm-cancellation).'
),
(
  'thm-neg-one-product',
  E'$(-1) \\cdot a = -a$',
  'theorem', 2,
  E'## Теорема: Умножение на $-1$\n\n**Утверждение:** Для любого $a \\in \\mathbb{F}$: $(-1) \\cdot a = -a$.\n\n**Доказательство:**\n\n$$a + (-1) \\cdot a = 1 \\cdot a + (-1) \\cdot a = (1 + (-1)) \\cdot a = 0 \\cdot a = 0$$\n\nИспользовались:\n- Аксиома нейтрального элемента умножения: $1 \\cdot a = a$\n- [Дистрибутивность](#axiom-distributivity)\n- [Произведение на ноль](#thm-zero-product): $0 \\cdot a = 0$\n\nТаким образом, $(-1) \\cdot a$ является противоположным к $a$. По [единственности противоположного](#thm-unique-inverse):\n$$(-1) \\cdot a = -a \\quad \\blacksquare$$'
)
ON CONFLICT (slug) DO NOTHING;

-- Теоремы уровня 3
INSERT INTO graph_node (slug, title, node_type, level, description) VALUES
(
  'thm-neg-product',
  E'$(-a) \\cdot b = -(a \\cdot b)$',
  'theorem', 3,
  E'## Теорема: Произведение противоположного элемента\n\n**Утверждение:** $(-a) \\cdot b = -(a \\cdot b)$.\n\n**Доказательство:**\n\n$$(-a) \\cdot b = ((-1) \\cdot a) \\cdot b = (-1) \\cdot (a \\cdot b) = -(a \\cdot b)$$\n\nПошагово:\n1. $(-a) = (-1) \\cdot a$ — по теореме [$(-1) \\cdot a = -a$](#thm-neg-one-product)\n2. Ассоциативность умножения\n3. Снова по теореме [$(-1) \\cdot a = -a$](#thm-neg-one-product)\n\n$\\blacksquare$'
),
(
  'thm-neg-neg-product',
  '$(-a)(-b) = ab$',
  'theorem', 3,
  E'## Теорема: Произведение двух противоположных элементов\n\n**Утверждение:** $(-a)(-b) = a \\cdot b$.\n\n**Доказательство:**\n\n$$(-a)(-b) = -(a \\cdot (-b)) = -(-(a \\cdot b)) = a \\cdot b$$\n\nПошагово:\n1. По теореме [$(-a) \\cdot b = -(ab)$](#thm-neg-product) с заменой $b \\to (-b)$\n2. По той же теореме: $a \\cdot (-b) = -(ab)$\n3. По теореме [двойного отрицания](#thm-double-negation)\n\n$\\blacksquare$'
)
ON CONFLICT (slug) DO NOTHING;

-- Рёбра (зависимости между узлами)
INSERT INTO graph_edge (from_node_id, to_node_id)
SELECT f.id, t.id FROM graph_node f, graph_node t
WHERE (f.slug, t.slug) IN (
  ('axiom-associativity-add',  'thm-unique-zero'),
  ('axiom-additive-identity',  'thm-unique-zero'),
  ('axiom-commutativity-add',  'thm-unique-zero'),
  ('axiom-associativity-add',  'thm-unique-inverse'),
  ('axiom-additive-identity',  'thm-unique-inverse'),
  ('axiom-additive-inverse',   'thm-unique-inverse'),
  ('axiom-commutativity-add',  'thm-cancellation'),
  ('axiom-associativity-add',  'thm-cancellation'),
  ('axiom-additive-inverse',   'thm-cancellation'),
  ('thm-unique-inverse',       'thm-double-negation'),
  ('axiom-additive-inverse',   'thm-double-negation'),
  ('axiom-distributivity',     'thm-zero-product'),
  ('axiom-additive-identity',  'thm-zero-product'),
  ('thm-cancellation',         'thm-zero-product'),
  ('thm-double-negation',      'thm-neg-one-product'),
  ('thm-zero-product',         'thm-neg-one-product'),
  ('thm-neg-one-product',      'thm-neg-product'),
  ('thm-neg-product',          'thm-neg-neg-product'),
  ('thm-double-negation',      'thm-neg-neg-product')
)
ON CONFLICT DO NOTHING;
