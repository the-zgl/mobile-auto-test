package com.daping.demoshop;

import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.Button;
import android.widget.ListView;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

/**
 * 商店页 + 收银台（购买 / 支付模块）。
 *
 * 支付流程刻意做成「下单 → 确认支付 → 回调 → 发货」两段式：
 * 点「购买」只是下单，必须再点「确认支付」才会扣款并发货，
 * 这样自动化用例才能分别断言「下单成功」和「支付成功」两个状态。
 * 余额不足时走异常分支，弹出「余额不足，支付失败」。
 */
public class MainActivity extends AppCompatActivity {

    public static final String PREFS = "demo_shop";
    public static final String KEY_BALANCE = "balance";

    /** 商品：名称 + 单价（分）。 */
    private static final String[][] ITEMS = {
            {"猫粮礼包", "300"},
            {"逗猫棒", "150"},
            {"猫抓板", "450"},
            {"小鱼干", "100"},
            {"猫窝", "800"},
    };

    /** 每一行商品的 resource-id（声明在 res/values/ids.xml），供自动化用例精准定位。 */
    private static final int[] ROW_IDS = {
            R.id.item_0, R.id.item_1, R.id.item_2, R.id.item_3, R.id.item_4,
    };

    private int balance;
    private TextView balanceText;
    private TextView paySuccess;
    private SharedPreferences prefs;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        prefs = getSharedPreferences(PREFS, MODE_PRIVATE);
        balance = prefs.getInt(KEY_BALANCE, LoginActivity.DEFAULT_BALANCE);

        balanceText = findViewById(R.id.tv_balance);
        paySuccess = findViewById(R.id.tv_pay_success);

        ListView list = findViewById(R.id.item_list);
        list.setAdapter(new ItemAdapter());

        refreshBalance();
    }

    private void refreshBalance() {
        balanceText.setText("余额：" + balance + " 分");
        // 进入页面（或余额变化）时清掉上一轮的支付结果提示，
        // 否则「取消支付不应出现成功提示」这类断言会被上一次的残留文案误伤。
        if (paySuccess != null) paySuccess.setText("");
    }

    /** 下单：弹出收银台确认框。 */
    private void createOrder(final String name, final int price) {
        new AlertDialog.Builder(this)
                .setTitle("收银台")
                .setMessage("商品：" + name + "\n金额：" + price + " 分")
                .setCancelable(true)
                .setPositiveButton("确认支付", new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface dialog, int which) {
                        pay(name, price);
                    }
                })
                .setNegativeButton("取消", null)
                .show();
    }

    /** 支付回调 + 发货：余额足够则扣款并提示成功，否则走失败分支。 */
    private void pay(String name, int price) {
        if (balance < price) {
            Toast.makeText(this, "余额不足，支付失败", Toast.LENGTH_SHORT).show();
            return;
        }

        balance -= price;
        prefs.edit().putInt(KEY_BALANCE, balance).apply();
        refreshBalance();

        paySuccess.setText("支付成功：" + name + " -" + price + " 分");
        Toast.makeText(this, "支付成功", Toast.LENGTH_SHORT).show();
    }

    /** 商品列表适配器：第 0 行的控件 id 固定为 item_0 / btn_buy。 */
    private class ItemAdapter extends BaseAdapter {

        @Override
        public int getCount() {
            return ITEMS.length;
        }

        @Override
        public Object getItem(int position) {
            return ITEMS[position];
        }

        @Override
        public long getItemId(int position) {
            return position;
        }

        @Override
        public View getView(int position, View convertView, ViewGroup parent) {
            View row = convertView;
            if (row == null) {
                row = LayoutInflater.from(MainActivity.this)
                        .inflate(R.layout.item_product, parent, false);
            }

            TextView name = row.findViewById(R.id.tv_item_name);
            TextView price = row.findViewById(R.id.tv_item_price);
            Button buy = row.findViewById(R.id.btn_buy);

            final String[] item = ITEMS[position];
            name.setText(item[0]);
            price.setText(item[1] + " 分");

            // 给每一行挂上稳定的 resource-id（item_0 ~ item_4，声明在 res/values/ids.xml），
            // 测试脚本才能用 By.id("...:id/item_0") 精准点到指定商品行
            row.setId(ROW_IDS[position % ROW_IDS.length]);

            // 购买按钮的 id 来自布局（@+id/btn_buy），每行一个，取第一个即为首行商品
            final int priceValue = Integer.parseInt(item[1]);
            buy.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    createOrder(item[0], priceValue);
                }
            });

            return row;
        }
    }
}
