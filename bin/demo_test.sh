
BASE=http://127.0.0.1:7860
# 既定シードの thread_id（DBブートストラップで作成）
TID_SEEDED_1=00000000000000000000000000   # "Welcome"
TID_SEEDED_2=00000000000000000000000001   # "Sample Research"



echo "# 一覧: 200"
curl -s $BASE/api/threads | jq

echo "# 作成: 201 → 新規ID取得"
TID_NEW=$(curl -s -X POST -H 'Content-Type: application/json' \
  -d '{"title":"API via curl"}' \
  $BASE/api/threads | jq -r '.id'); echo $TID_NEW

echo "# メッセージ一覧（200, seeded）"
curl -s $BASE/api/threads/$TID_SEEDED_1/messages | jq

echo "# メッセージ一覧（404）"
curl -i $BASE/api/threads/ffffffffffffffffffffffffffff/messages | head -n1

echo "# メッセージ追加（201, user）"
curl -i -s -X POST -H 'Content-Type: application/json' \
  -d '{"role":"user","content":"Hello from curl"}' \
  $BASE/api/threads/$TID_NEW/messages | head -n1

echo "# メッセージ追加（201, assistant）"
curl -i -s -X POST -H 'Content-Type: application/json' \
  -d '{"role":"assistant","content":"Hi! This is assistant."}' \
  $BASE/api/threads/$TID_NEW/messages | head -n1

echo "# タイトル変更（200）"
curl -s -X PATCH -H 'Content-Type: application/json' \
  -d '{"title":"Renamed via curl"}' \
  $BASE/api/threads/$TID_NEW | jq

echo "# アーカイブ（200）"
curl -s -X PATCH -H 'Content-Type: application/json' \
  -d '{"archived": true}' \
  $BASE/api/threads/$TID_NEW | jq

echo "# 削除（204）"
curl -i -X DELETE $BASE/api/threads/$TID_NEW | head -n1

echo "# 削除後のGET（404）"
curl -i $BASE/api/threads/$TID_NEW/messages | head -n1



echo "# 取得（200）"
curl -s $BASE/api/settings/app | jq

echo "# 更新（200）"
curl -s -X PATCH -H 'Content-Type: application/json' \
  -d '{"show_thread_sidebar": false, "show_threads_tab": true}' \
  $BASE/api/settings/app | jq

