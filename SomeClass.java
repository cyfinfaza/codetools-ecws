import java.util.ArrayList;

class SomeClass{
	private static int val = 6;
	private static ArrayList<Integer> list = new ArrayList<Integer>();
	public static int getVal(){
		return val;
	}
	public static void setVal(int toSet){
		val = toSet;
	}
	public static void addToList(int toAdd){
		list.add(toAdd);
	}
	public static ArrayList<Integer> getList(){
		return list;
	}
}