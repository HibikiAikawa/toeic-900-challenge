# TOEIC-900-Challenge

## 🎯 目的
3ヶ月で **1000問** を解き切り、TOEIC 900 点を目指す。  
毎日 GitHub Issue から入力 → 自動で以下を算出・公開します。

- 当日実行量  
- 完全理解数  
- 週次合計  
- 進捗率  
- 90日到達予測  

---

## ✅ 成果物（完成の定義）
- Issue フォームから日次入力 → `logs/daily.csv` に記録  
- `summary.py` が KPI を算出し README を更新  
- GitHub Actions が  
  - 日次 Issue 作成時  
  - 毎晩 JST21:30  
  に自動集計を実行  
- X (Twitter) へ自動またはワンクリックで投稿  
- README に直近 KPI が表示される  

---

## 📊 今日のKPI
<!--KPIS-->
（ここを `summary.py` が上書き）
<!--/KPIS-->

---

## 📂 ディレクトリ構成

```
toeic-900-challenge/
├─ README.md
├─ logs/
│  └─ daily.csv
├─ scripts/
│  ├─ summary.py
│  └─ tweet.py
└─ .github/
├─ ISSUE_TEMPLATE/
│  └─ daily.yml
└─ workflows/
├─ on-daily-issue.yml
└─ nightly-recalc.yml
```

---

## 📝 運用方法
1. GitHub Issue フォーム「Daily Log」から当日の実績を入力  
2. Actions が自動で集計 → README を更新 → （任意で X に投稿）  
3. 夜の定時再集計で週次や予測も反映  

---

## 🔑 Secrets（必要なら）
- `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_SECRET`  
  （X 自動投稿用）  
- `SLACK_WEBHOOK_URL`（任意で Slack 通知）

---

## ⚠️ 注意
- 入力は必ず **数値** で（日付は `YYYY-MM-DD`）  
- 公開リポジトリなので個人情報やスクショは避ける  
- 入力忘れ時は `missed` ラベル等でリマインド機能を追加予定  

---

## 📌 今後の拡張アイデア
- 週次 PNG グラフ生成  
- Slack 通知  
- note への週次まとめテンプレ生成  
- 「入力漏れ」検出とリマインド通知  

---

## 💡 このリポジトリの意義
このリポジトリは **学習ログを公開し、外部からの拘束力を得るための仕組み** です。  
毎日の積み上げを **定量的に可視化し、発信する** ことで、3ヶ月間で 1000 問を解き切り、TOEIC 900 点を達成することを狙います。  

継続こそ最大の武器。ここに全てを記録していきます。  

---