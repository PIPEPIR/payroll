import streamlit as st
import pandas as pd
import io
import math

st.set_page_config(page_title="ระบบคิดเงินเดือนร้านอาหาร", page_icon="📝")

st.title("📝 ระบบคิดเงินเดือน")
st.write("เริ่มกะ 14.00 น. | สายไม่เกิน 14.30 หักนาทีละ 5 ฿ | สายเกิน 14.30 หักนาทีละ 10 ฿")

hourly_rate = st.number_input("เรทค่าจ้างต่อชั่วโมง (บาท):", min_value=1, value=50, step=5)
uploaded_files = st.file_uploader("อัปโหลดไฟล์ Excel ของพนักงาน", type=["xlsx"], accept_multiple_files=True)

if uploaded_files:
    all_employees_summary = [] 
    st.divider()
    
    for file in uploaded_files:
        st.subheader(f"👤 พนักงาน/ไฟล์: {file.name}")
        
        try:
            df = pd.read_excel(file)
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            df = df.sort_values('Timestamp').reset_index(drop=True)
            df['Date'] = df['Timestamp'].dt.date
            
            daily_records = []
            total_hours_person = 0
            total_penalty_person = 0 # เก็บยอดโดนหักรวม
            
            for date, group in df.groupby('Date'):
                punches = group['Timestamp'].tolist()
                
                if len(punches) % 2 != 0:
                    st.warning(f"⚠️ วันที่ {date}: มีการตอกบัตร {len(punches)} ครั้ง ระบบจะคิดเฉพาะคู่ที่สมบูรณ์")
                
                # ==========================================
                # ระบบคำนวณหักเงินมาสาย (ดูจากการตอกบัตรรอบแรกของวัน)
                # ==========================================
                first_punch = punches[0]
                shift_start_time = first_punch.replace(hour=14, minute=0, second=0, microsecond=0)
                
                daily_penalty = 0
                late_mins = 0
                
                # ถ้าตอกบัตรเข้างานหลัง 14:00 น.
                if first_punch > shift_start_time:
                    late_delta = first_punch - shift_start_time
                    # ปัดเศษนาทีลง (ถ้ามา 14:00:59 ถือว่าไม่สาย)
                    late_mins = math.floor(late_delta.total_seconds() / 60) 
                    
                    if late_mins > 0:
                        if late_mins <= 30:
                            daily_penalty = late_mins * 5
                        else:
                            # 30 นาทีแรก นาทีละ 5 บาท + นาทีที่เกิน 30 นาทีละ 10 บาท
                            daily_penalty = (30 * 5) + ((late_mins - 30) * 10)
                
                total_penalty_person += daily_penalty

                # ==========================================
                # คำนวณชั่วโมงทำงานปกติ
                # ==========================================
                daily_hours = 0
                for i in range(0, len(punches) - 1, 2):
                    time_in = punches[i]
                    time_out = punches[i+1]
                    hours = (time_out - time_in).total_seconds() / 3600
                    daily_hours += hours
                
                daily_hours = round(daily_hours, 2)
                total_hours_person += daily_hours
                
                daily_records.append({
                    'วันที่': date,
                    'เวลาเข้างาน (รอบแรก)': first_punch.strftime('%H:%M:%S'),
                    'สาย (นาที)': late_mins,
                    'โดนหัก (บาท)': daily_penalty,
                    'ชั่วโมงทำงานรวม': daily_hours
                })
            
            # แสดงตารางรายวัน
            if daily_records:
                with st.expander(f"ดูรายละเอียดรายวัน ของ {file.name}"):
                    st.dataframe(pd.DataFrame(daily_records))
            
            # สรุปยอดเงินของคนนี้
            base_pay = total_hours_person * hourly_rate
            net_pay = base_pay - total_penalty_person
            
            st.success(f"ทำงาน: {total_hours_person:.2f} ชม. | ค่าจ้าง: ฿{base_pay:,.2f} | โดนหักสาย: ฿{total_penalty_person:,.2f} | **รับสุทธิ: ฿{net_pay:,.2f}**")
            st.write("---")
            
            all_employees_summary.append({
                "ชื่อไฟล์ (พนักงาน)": file.name,
                "ชั่วโมงทำงาน (ชม.)": total_hours_person,
                "ค่าจ้างปกติ (บาท)": base_pay,
                "หักมาสาย (บาท)": total_penalty_person,
                "รับเงินสุทธิ (บาท)": net_pay
            })
            
        except Exception as e:
            st.error(f"ไฟล์ {file.name} มีปัญหา (Error: {e})")

    # สรุปยอดรวมทุกคน
    if all_employees_summary:
        st.header("💰 สรุปยอดจ่ายเงินพนักงานทั้งหมด")
        summary_df = pd.DataFrame(all_employees_summary)
        st.dataframe(summary_df, use_container_width=True)
        
        grand_total = summary_df['รับเงินสุทธิ (บาท)'].sum()
        st.metric("ยอดเงินรวมที่ร้านต้องโอนจ่าย (บาท)", f"฿{grand_total:,.2f}")