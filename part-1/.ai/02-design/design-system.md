# Design System v2 (Landing, compact)

Цель: быстрый и надежный старт верстки лендинга за 15 минут без сложных визуальных зависимостей.

## 1) Базовые CSS Variables

```css
:root {
  /* Colors */
  --color-bg-canvas: #f4f3ef;
  --color-surface: #ffffff;
  --color-text-primary: #111111;
  --color-text-secondary: #4c4c4c;
  --color-border-soft: #e8e6de;
  --color-brand-primary: #37be6c;
  --color-brand-primary-hover: #2fa65f;
  --color-accent-lime: #e5ec4a;

  /* Typography */
  --font-heading: "Sora", "Avenir Next", "Segoe UI", sans-serif;
  --font-body: "Manrope", "SF Pro Text", "Segoe UI", sans-serif;

  --fs-h1: 56px;
  --lh-h1: 1.1;
  --fs-h2: 40px;
  --lh-h2: 1.15;
  --fs-h3: 28px;
  --lh-h3: 1.2;
  --fs-body: 18px;
  --lh-body: 1.6;
  --fs-caption: 14px;
  --lh-caption: 1.4;
  --fs-button: 16px;
  --lh-button: 1.2;

  /* Spacing */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 24px;
  --space-6: 32px;
  --space-7: 48px;
  --space-8: 64px;

  /* Radius / border / shadows */
  --radius-sm: 10px;
  --radius-md: 14px;
  --radius-lg: 20px;
  --radius-pill: 999px;
  --border-default: 1px solid var(--color-border-soft);
  --shadow-card: 0 6px 18px rgba(17, 17, 17, 0.08);
  --shadow-soft: 0 2px 8px rgba(17, 17, 17, 0.05);

  /* Motion */
  --duration-fast: 150ms;
  --duration-base: 220ms;
  --ease-standard: ease-out;
  --opacity-disabled: 0.45;
}
```

## 2) Цветовые токены (8)

| Токен | Hex | Где применять |
|---|---|---|
| `--color-bg-canvas` | `#F4F3EF` | Фон страницы и крупных секций |
| `--color-surface` | `#FFFFFF` | Карточки, формы, навбар, внутренние контейнеры |
| `--color-text-primary` | `#111111` | Заголовки, ключевые CTA-тексты |
| `--color-text-secondary` | `#4C4C4C` | Обычный текст, подписи в блоках |
| `--color-border-soft` | `#E8E6DE` | Бордеры карточек, инпутов, разделителей |
| `--color-brand-primary` | `#37BE6C` | Primary-кнопки, активные элементы формы |
| `--color-brand-primary-hover` | `#2FA65F` | Hover для primary-кнопок |
| `--color-accent-lime` | `#E5EC4A` | Badge/highlight, декоративные акценты |

## 3) Типографика

| Стиль | Параметры | Использование |
|---|---|---|
| `H1` | `56/1.1`, `700`, `var(--font-heading)` | Главный оффер hero |
| `H2` | `40/1.15`, `700`, `var(--font-heading)` | Заголовки секций |
| `H3` | `28/1.2`, `600`, `var(--font-heading)` | Подзаголовки карточек/колонок |
| `Body` | `18/1.6`, `400`, `var(--font-body)` | Основные абзацы |
| `Caption` | `14/1.4`, `500`, `var(--font-body)` | Подписи, метаданные, helper-текст |
| `Button` | `16/1.2`, `600`, `var(--font-body)` | Текст кнопок |

Адаптив быстро и безопасно:
- До `1024px`: `H1 48px`, `H2 34px`, `H3 24px`, `Body 17px`
- До `640px`: `H1 38px`, `H2 30px`, `H3 22px`, `Body 16px`

## 4) Spacing Scale

Базовая шкала: `4 / 8 / 12 / 16 / 24 / 32 / 48 / 64`

Рекомендации:
- Внутри компонента: `8-16px`
- Между элементами в секции: `16-32px`
- Отступы секции по вертикали: `48-64px`

## 5) Компоненты

### Button
- Размер по умолчанию: высота `48px`, padding `0 24px`, `border-radius: var(--radius-pill)`
- Primary: фон `--color-brand-primary`, текст `--color-surface`
- Secondary: фон `--color-surface`, текст `--color-text-primary`, бордер `--border-default`
- `transition: background-color var(--duration-fast) var(--ease-standard), opacity var(--duration-fast) var(--ease-standard)`

### Section
- Контейнер: `max-width: 1200px`, центрирование, горизонтальные паддинги `24px` (desktop), `16px` (mobile)
- Вертикальный ритм: `padding-block: var(--space-7)` desktop / `var(--space-6)` mobile
- Фон: `--color-bg-canvas` или `--color-surface` (чередование для читабельности)

### Card
- Фон `--color-surface`, бордер `--border-default`, радиус `--radius-md`
- Padding `24px`, тень `--shadow-soft` (или `--shadow-card` для важных карточек)
- Структура: `H3 + body + action/метрика`

### Badge
- Минимальная высота `28px`, padding `6px 12px`, `border-radius: var(--radius-pill)`
- Варианты:
  - Neutral: фон `--color-surface`, текст `--color-text-secondary`, бордер `--border-default`
  - Accent: фон `--color-accent-lime`, текст `--color-text-primary`

### Input / Form
- Input высота `48px`, радиус `--radius-sm`, бордер `--border-default`, фон `--color-surface`
- Фокус: `border-color: var(--color-brand-primary)`, мягкая тень `0 0 0 3px rgba(55,190,108,0.2)`
- Вертикальный gap формы: `12px`, между группами `24px`
- Кнопка submit использует `Button primary`

### Testimonial
- Контейнер как Card (`--radius-md`, `--shadow-soft`, `24px`)
- Состав: цитата (`Body`), автор (`H3` или semibold body), роль (`Caption`)
- Для сетки: 1 колонка на mobile, 2-3 на desktop

## 6) Состояния кнопок

| State | Primary | Secondary |
|---|---|---|
| `default` | фон `--color-brand-primary`, текст `--color-surface` | фон `--color-surface`, текст `--color-text-primary`, бордер `--border-default` |
| `hover` | фон `--color-brand-primary-hover` | фон `--color-bg-canvas` |
| `disabled` | `opacity: var(--opacity-disabled)`, `cursor: not-allowed`, без тени | `opacity: var(--opacity-disabled)`, `cursor: not-allowed`, без тени |

## 7) Радиусы, бордеры, тени

- Радиусы:
  - `--radius-sm: 10px` (input, small card)
  - `--radius-md: 14px` (cards, testimonials)
  - `--radius-lg: 20px` (крупные контейнеры/hero blocks)
  - `--radius-pill: 999px` (кнопки и badge)
- Бордер:
  - Базовый: `--border-default`
- Тени:
  - `--shadow-soft` для повседневных карточек
  - `--shadow-card` для акцентных блоков

## 8) Простые анимации (быстро в верстке)

1. `fade-up` для секций при появлении:
   - `opacity: 0 -> 1`, `transform: translateY(8px) -> translateY(0)`, `220ms`
2. `button-press`:
   - при `:active` `transform: translateY(1px)`, `150ms`
3. `card-hover-lift`:
   - на `:hover` `transform: translateY(-2px)`, тень `--shadow-soft -> --shadow-card`, `150ms`

Обязательный fallback:
- Для `@media (prefers-reduced-motion: reduce)` отключать `transform/transition`.

