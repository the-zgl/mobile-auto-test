package com.daping.demoshop;

import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.text.TextUtils;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;

/**
 * 登录页（账号模块）。
 *
 * 这是一个「故意做得可测」的 App：
 * 每个可交互控件都带稳定的 resource-id，测试脚本不必依赖 XPath 猜层级。
 * 账号固定为 user1 / 123456，用于覆盖登录成功与密码错误两条用例。
 */
public class LoginActivity extends AppCompatActivity {

    /** 内置测试账号，真正的项目里会走服务端接口。 */
    public static final String VALID_USER = "user1";
    public static final String VALID_PASSWORD = "123456";

    /** 默认余额（分）。 */
    public static final int DEFAULT_BALANCE = 1000;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_login);

        final EditText username = findViewById(R.id.username);
        final EditText password = findViewById(R.id.password);
        final TextView error = findViewById(R.id.error);
        Button login = findViewById(R.id.login);

        login.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                String user = username.getText().toString().trim();
                String pass = password.getText().toString().trim();

                if (TextUtils.isEmpty(user) || TextUtils.isEmpty(pass)) {
                    error.setText("请输入账号和密码");
                    return;
                }

                if (VALID_USER.equals(user) && VALID_PASSWORD.equals(pass)) {
                    error.setText("");
                    // 只在首次登录时初始化余额，保证「重复点击登录」不会把余额重置
                    SharedPreferences sp = getSharedPreferences(MainActivity.PREFS, MODE_PRIVATE);
                    if (!sp.contains(MainActivity.KEY_BALANCE)) {
                        sp.edit().putInt(MainActivity.KEY_BALANCE, DEFAULT_BALANCE).apply();
                    }
                    startActivity(new Intent(LoginActivity.this, MainActivity.class));
                } else {
                    error.setText("密码错误，请重新输入");
                }
            }
        });
    }
}
