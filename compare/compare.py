from flask import Flask, request, render_template_string
import pymysql
import pymysql.cursors

app = Flask(__name__)

# 数据库配置：请根据你的设置进行调整
db_config = {
    'host': 'gz-cdb-5scrcjb5.sql.tencentcdb.com',
    'user': 'db',
    'password': 'dbdb905905',
    'db': 'sele',
    'port': 63432,
    'charset': 'utf8mb4',
    "cursorclass": pymysql.cursors.DictCursor
}

def query_data(tender_id, table_name):
    connection = pymysql.connect(**db_config)
    try:
        with connection.cursor() as cursor:
            sql = f"SELECT * FROM `{table_name}` WHERE tender_id = %s"
            cursor.execute(sql, (tender_id,))
            result = cursor.fetchone()
            return result
    finally:
        connection.close()

@app.route('/')
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>数据比较</title>
    </head>
    <body>
        <h2>输入Tender ID进行比较</h2>
        <input type="number" id="tenderId" placeholder="Tender ID">
        <button onclick="compareData()">比较数据</button>
        <div id="comparisonResult"></div>
        <div id="scoringButtons"></div> <!-- 容纳评分按钮的容器 -->

        <script>
            function compareData() {
                var tenderId = document.getElementById('tenderId').value;
                fetch(`/compare?tender_id=${tenderId}`)
                    .then(response => response.text())
                    .then(html => {
                        document.getElementById('comparisonResult').innerHTML = html;
                        // 生成评分按钮
                        generateScoringButtons(tenderId);
                    })
                    .catch(error => console.error('Error:', error));
            }

            function generateScoringButtons(tenderId) {
                var buttonsHtml = `
                    <button onclick="score('tender_detail', '${tenderId}')">tender_detail 更好</button>
                    <button onclick="score('tender_detail_copy', '${tenderId}')">tender_detail_copy 更好</button>
                    <button onclick="score('none', '${tenderId}')">都不选</button>
                `;
                document.getElementById('scoringButtons').innerHTML = buttonsHtml;
            }

            function score(selected_table, tenderId) {
                fetch(`/score`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: `tender_id=${tenderId}&selected_table=${selected_table}`
                })
                .then(response => {
                    if (response.ok) {
                        return response.text();
                    }
                    throw new Error('Request failed!');
                })
                .then(data => {
                    alert(data);
                    compareData(); // 重新加载比较数据和评分按钮
                })
                .catch(error => console.error('Error:', error));
            }
        </script>
    </body>
    </html>
    """)

@app.route('/compare', methods=['GET'])
def compare():
    tender_id = request.args.get('tender_id')
    if tender_id:
        data_detail = query_data(tender_id, 'tender_detail')
        data_detail_copy = query_data(tender_id, 'tender_detail_copy')
        
        table_html = "<table border='1'><tr><th>字段名</th><th>tender_detail值</th><th>tender_detail_copy值</th></tr>"
        
        if data_detail and data_detail_copy:
            for key in data_detail.keys():
                original_value = data_detail.get(key, "")
                copy_value = data_detail_copy.get(key, "")
                table_html += f"<tr><td>{key}</td><td>{original_value}</td><td>{copy_value}</td></tr>"
        else:
            table_html += "<tr><td colspan='3'>没有找到数据</td></tr>"
        
        table_html += "</table>"
        return table_html
    else:
        return "tender_id is required", 400

@app.route('/score', methods=['POST'])
def score():
    tender_id = request.form['tender_id']
    selected_table = request.form['selected_table']  # "tender_detail", "tender_detail_copy", or "none"
    
    # 连接数据库并尝试更新或插入评分
    connection = pymysql.connect(**db_config)
    try:
        with connection.cursor() as cursor:
            # 检查是否已存在评分
            sql_check = "SELECT * FROM tender_scores WHERE tender_id = %s AND selected_table = %s"
            cursor.execute(sql_check, (tender_id, selected_table))
            if cursor.fetchone() is None:
                # 插入新评分
                sql_insert = "INSERT INTO tender_scores (tender_id, selected_table, score) VALUES (%s, %s, %s)"
                cursor.execute(sql_insert, (tender_id, selected_table, 1))
            # 无需更新逻辑，因为分数不叠加
        connection.commit()
    finally:
        connection.close()
    
    return "Scored successfully"

# 更新compare路由以包括评分信息
# 在compare函数中，查询`tender_scores`表来获取累计分数，并将其包含在返回的HTML中。



if __name__ == '__main__':
    app.run(debug=True)